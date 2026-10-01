"""Panel 1의 예비 Geometry. Isaac Sim 내부에서 import하여 사용한다."""

import hashlib
import json
from pathlib import Path

from pxr import Gf, Sdf, Usd, UsdGeom, UsdLux, UsdShade

ROOT = Path(__file__).resolve().parents[2]
CONFIG = ROOT / "config/panel_1_geometry.json"
ASSET = ROOT / "isaac_sim/assets/cp_panel/panel_1_geometry.usda"
SCENE = ROOT / "isaac_sim/stages/panel_1_preview.usda"
GENERATOR = "press-cp-digital-twin/panel_1_geometry/v1"


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read_config():
    cfg = json.loads(CONFIG.read_text(encoding="utf-8"))
    if [m["id"] for m in cfg["modules"]] != ["temperature", "pressure", "vacuum"]:
        raise ValueError("온도·압력·진공 모듈 순서를 확인하세요.")
    if cfg["geometry"]["meters_per_pixel"] <= 0:
        raise ValueError("임시 크기 배율은 양수여야 합니다.")
    for module in cfg["modules"]:
        if [s["id"] for s in module["slots"]] != ["slot_1", "slot_2"]:
            raise ValueError("각 모듈에는 위·아래 두 Slot이 필요합니다.")
        for box in [module["bbox_px"], *(s["bbox_px"] for s in module["slots"])]:
            if not (box[0] < box[2] and box[1] < box[3]):
                raise ValueError(f"잘못된 bbox: {box}")
    return cfg


def box_geometry(cfg, bbox, depth, y):
    left, top, right, bottom = bbox
    ox, oy = cfg["reference"]["origin_px"]
    scale = cfg["geometry"]["meters_per_pixel"]
    center = ((left + right - 2 * ox) * scale / 2, y, (2 * oy - top - bottom) * scale / 2)
    size = ((right - left) * scale, depth, (bottom - top) * scale)
    return center, size


def new_stage(root_path):
    stage = Usd.Stage.CreateInMemory()
    UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.z)
    UsdGeom.SetStageMetersPerUnit(stage, 1.0)
    root = UsdGeom.Xform.Define(stage, root_path).GetPrim()
    stage.SetDefaultPrim(root)
    stage.GetRootLayer().customLayerData = {
        "generator": GENERATOR,
        "config_sha256": sha256(CONFIG),
        "generator_sha256": sha256(__file__),
        "dimensions_status": "temporary_not_measured",
        "reference_frame_seconds": 4.0,
        "use": "preliminary_geometry_not_training_data",
    }
    return stage


def materials(stage, root, cfg):
    result = {}
    for name, settings in cfg["preview"]["materials"].items():
        material = UsdShade.Material.Define(stage, f"{root}/Looks/{name}")
        shader = UsdShade.Shader.Define(stage, f"{material.GetPath()}/Shader")
        shader.CreateIdAttr("UsdPreviewSurface")
        shader.CreateInput("diffuseColor", Sdf.ValueTypeNames.Color3f).Set(Gf.Vec3f(*settings["color"]))
        shader.CreateInput("roughness", Sdf.ValueTypeNames.Float).Set(settings["roughness"])
        material.CreateSurfaceOutput().ConnectToSource(shader.ConnectableAPI(), "surface")
        result[name] = material
    return result


def cube(stage, path, center, size, material):
    shape = UsdGeom.Cube.Define(stage, path)
    shape.CreateSizeAttr(1.0)
    shape.AddTranslateOp().Set(Gf.Vec3d(*center))
    shape.AddScaleOp().Set(Gf.Vec3f(*size))
    UsdShade.MaterialBindingAPI.Apply(shape.GetPrim()).Bind(material)
    return shape.GetPrim()


def export_owned(stage, path):
    if path.exists():
        layer = Sdf.Layer.FindOrOpen(str(path))
        if layer.customLayerData.get("generator") != GENERATOR:
            raise FileExistsError(f"자동 생성 파일이 아니므로 덮어쓰지 않습니다: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    if not stage.GetRootLayer().Export(str(path)):
        raise RuntimeError(f"USD 저장 실패: {path}")
    existing = Sdf.Layer.Find(str(path))
    if existing:
        existing.Reload()


def build():
    cfg = read_config()
    geom = cfg["geometry"]
    asset = new_stage("/Panel1")
    mats = materials(asset, "/Panel1", cfg)
    center, size = box_geometry(cfg, geom["backboard_bbox_px"], geom["backboard_depth_m"], geom["backboard_depth_m"] / 2)
    cube(asset, "/Panel1/Backboard", center, size, mats["backboard"])
    depth = geom["module_depth_m"]
    face_y = -depth - geom["face_gap_m"] - geom["slot_depth_m"] / 2
    for module in cfg["modules"]:
        path = f'/Panel1/{module["id"]}'
        prim = UsdGeom.Xform.Define(asset, path).GetPrim()
        prim.SetCustomDataByKey("module_id", module["id"])
        center, size = box_geometry(cfg, module["bbox_px"], depth, -depth / 2)
        cube(asset, f"{path}/Body", center, size, mats["body"])
        for slot in module["slots"]:
            center, size = box_geometry(cfg, slot["bbox_px"], geom["slot_depth_m"], face_y)
            prim = cube(asset, f'{path}/{slot["id"]}', center, size, mats[slot["material"]])
            prim.SetCustomDataByKey("slot_id", f'panel_1/{module["id"]}/{slot["id"]}')
            prim.SetCustomDataByKey("status", "placeholder_no_digits")
        if "control_bbox_px" in module:
            center, size = box_geometry(cfg, module["control_bbox_px"], geom["slot_depth_m"], face_y)
            cube(asset, f"{path}/Controls", center, size, mats["controls"])
    export_owned(asset, ASSET)

    scene = new_stage("/World")
    # 상대 Asset 참조를 Scene 파일 위치에서 해석하도록 먼저 파일에 위치를 부여한다.
    export_owned(scene, SCENE)
    scene = Usd.Stage.Open(str(SCENE))
    panel = UsdGeom.Xform.Define(scene, "/World/Panel1").GetPrim()
    panel.GetReferences().AddReference("../assets/cp_panel/panel_1_geometry.usda")
    cam_cfg = cfg["preview"]["camera"]
    cam = UsdGeom.Camera.Define(scene, "/World/ReviewCamera")
    cam.CreateProjectionAttr(UsdGeom.Tokens.orthographic)
    # USD aperture는 Stage 단위의 1/10. Stage 단위는 1 m.
    cam.CreateHorizontalApertureAttr(cam_cfg["horizontal_span_m"] * 10)
    cam.CreateVerticalApertureAttr(cam_cfg["vertical_span_m"] * 10)
    cam.CreateClippingRangeAttr(Gf.Vec2f(0.01, 10.0))
    cam.AddTranslateOp().Set(Gf.Vec3d(*cam_cfg["position_m"]))
    cam.AddRotateXYZOp().Set(Gf.Vec3f(*cam_cfg["rotation_xyz_deg"]))
    light = UsdLux.DomeLight.Define(scene, "/World/ReviewLight")
    light.CreateIntensityAttr(cfg["preview"]["dome_intensity"])
    export_owned(scene, SCENE)
    return cfg


def validate(stage):
    """저장 후 실제 합성 Stage의 축·단위·수량·배치·경계를 검사한다."""
    if not stage or UsdGeom.GetStageUpAxis(stage) != UsdGeom.Tokens.z:
        raise AssertionError("Stage는 Z-up이어야 합니다.")
    if UsdGeom.GetStageMetersPerUnit(stage) != 1.0:
        raise AssertionError("Stage 단위는 1 m여야 합니다.")
    panel = stage.GetPrimAtPath("/World/Panel1")
    expected = ["temperature", "pressure", "vacuum"]
    modules = [p for p in panel.GetChildren() if p.GetCustomDataByKey("module_id")]
    if sorted(p.GetName() for p in modules) != sorted(expected):
        raise AssertionError("세 모듈 구성이 일치하지 않습니다.")
    cache = UsdGeom.BBoxCache(Usd.TimeCode.Default(), [UsdGeom.Tokens.default_])

    def bounds(path):
        prim = stage.GetPrimAtPath(path)
        if not prim or not prim.IsA(UsdGeom.Cube):
            raise AssertionError(f"Cube 누락: {path}")
        return cache.ComputeWorldBound(prim).ComputeAlignedRange()

    records, centers, slot_ids = [], [], []
    for name in expected:
        path = f"/World/Panel1/{name}"
        body = bounds(f"{path}/Body")
        centers.append(body.GetMidpoint()[0])
        slots = []
        for slot_name in ["slot_1", "slot_2"]:
            slot_path = f"{path}/{slot_name}"
            box = bounds(slot_path)
            sid = stage.GetPrimAtPath(slot_path).GetCustomDataByKey("slot_id")
            if sid != f"panel_1/{name}/{slot_name}":
                raise AssertionError(f"Slot ID 오류: {sid}")
            slot_ids.append(sid)
            for axis in [0, 2]:
                if box.GetMin()[axis] < body.GetMin()[axis] or box.GetMax()[axis] > body.GetMax()[axis]:
                    raise AssertionError(f"표시 영역이 모듈 밖으로 벗어남: {slot_path}")
            if box.GetMax()[1] >= body.GetMin()[1]:
                raise AssertionError(f"표시 영역이 전면에 있지 않음: {slot_path}")
            slots.append(box)
        if slots[0].GetMin()[2] <= slots[1].GetMax()[2]:
            raise AssertionError(f"위·아래 영역 겹침 또는 역전: {name}")
        records.append({"module": name, "body_size_m": list(body.GetSize()), "upper_above_lower": True})
    if not centers[0] < centers[1] < centers[2]:
        raise AssertionError("온도·압력·진공의 좌우 순서 오류")
    actual_slots = [p for p in stage.Traverse() if p.GetCustomDataByKey("slot_id")]
    if len(actual_slots) != 6 or len(set(slot_ids)) != 6:
        raise AssertionError("Slot 수 또는 중복 오류")
    return {"up_axis": "Z", "meters_per_unit": 1.0, "module_count": 3, "slot_count": 6, "modules": records}
