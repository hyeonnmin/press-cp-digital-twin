"""Session Layer에서 숫자 Mesh 속성만 갱신한다. 원본 Asset은 저장하지 않는다."""
import hashlib
import json
from pxr import Usd, UsdGeom, UsdShade
import press_cp_environment as geometry

ATTRIBUTES = ("points", "faceVertexCounts", "faceVertexIndices")


def mesh_signature(stage, path):
    root = stage.GetPrimAtPath(path)
    path = root.GetCustomDataByKey("generated_mesh_root") or path
    data = {}
    for name in ("Lit", "Unlit"):
        prim = stage.GetPrimAtPath(f"{path}/{name}")
        data[name] = {attr: str(prim.GetAttribute(attr).Get()) for attr in ATTRIBUTES}
    return hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()


def update(stage, cfg, frame):
    slots = {p.GetCustomDataByKey("slot_id"): p for p in stage.Traverse() if p.GetCustomDataByKey("slot_id")}
    requested = {row["slot_id"]: row["text"] for row in frame["slots"]}
    if len(requested) != 42 or len(frame["slots"]) != 42 or set(requested) != set(slots):
        raise ValueError("42개 Slot ID 연결 불일치")
    templates = Usd.Stage.CreateInMemory()
    mat = UsdShade.Material.Define(templates, "/Material")
    checks = []
    with Usd.EditContext(stage, stage.GetSessionLayer()):
        for panel in cfg["panels"]:
            for module in panel["modules"]:
                _, width, height = geometry.image_box(cfg, module["bbox"], -0.026)
                vac = module["id"] == "vacuum"
                display = cfg["display"]
                sw = width * display["vacuum_main_width" if vac else "main_width"]
                dh = height * display["vacuum_digit_height" if vac else "digit_height"]
                for index in (1, 2):
                    sid = f"{panel['id']}/{module['id']}/slot_{index}"
                    text = requested[sid]
                    if not text or any(c not in "0123456789.-" for c in text):
                        raise ValueError("지원하지 않는 표시 문자열")
                    path = str(slots[sid].GetPath())
                    template = f"/Template_{len(checks)}"
                    geometry.digits(templates, template, text, [0, 0, 0], sw, dh, mat, mat)
                    previous = slots[sid].GetCustomDataByKey("generated_mesh_root")
                    generation = int(slots[sid].GetCustomDataByKey("mesh_generation") or 0) + 1
                    generated = f"{path}/Generated_{generation}"
                    if previous:
                        stage.GetPrimAtPath(previous).SetActive(False)
                    UsdGeom.Xform.Define(stage, generated)
                    slots[sid].SetCustomDataByKey("generated_mesh_root", generated)
                    slots[sid].SetCustomDataByKey("mesh_generation", generation)
                    for name in ("Lit", "Unlit"):
                        source = templates.GetPrimAtPath(f"{template}/{name}")
                        if not source:
                            empty = UsdGeom.Mesh.Define(templates, f"{template}/{name}")
                            empty.CreatePointsAttr([]); empty.CreateFaceVertexCountsAttr([]); empty.CreateFaceVertexIndicesAttr([])
                            source = empty.GetPrim()
                        UsdGeom.Imageable(stage.GetPrimAtPath(f"{path}/{name}")).CreateVisibilityAttr().Set("invisible")
                        material_name = ("green_led" if index == 1 else "amber_led") if name == "Lit" else "off_segment"
                        material = UsdShade.Material.Get(stage, f"/World/Cabinet/Looks/{material_name}")
                        geometry.mesh(stage, f"{generated}/{name}", *[source.GetAttribute(attr).Get() for attr in ATTRIBUTES], material)
                    slots[sid].SetCustomDataByKey("display_text", text)
                    slots[sid].SetCustomDataByKey("text_status", "synthetic_generated")
                    actual = mesh_signature(stage, path)
                    if actual != mesh_signature(templates, template):
                        # 빈 Unlit도 비교할 수 있게 템플릿에 빈 Mesh를 만든다.
                        if not templates.GetPrimAtPath(template + "/Unlit"):
                            empty = UsdGeom.Mesh.Define(templates, template + "/Unlit")
                            empty.CreatePointsAttr([]); empty.CreateFaceVertexCountsAttr([]); empty.CreateFaceVertexIndicesAttr([])
                        if actual != mesh_signature(templates, template):
                            raise AssertionError(f"Mesh 갱신 실패: {sid}")
                    checks.append({"slot_id": sid, "text": text, "mesh_sha256": actual, "prim_path": path})
    return checks
