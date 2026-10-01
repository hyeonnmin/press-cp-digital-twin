"""Standalone 소규모 Mesh 갱신·이미지/정답 동기화 검증."""
import argparse
import asyncio
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))


async def run(indices):
    import carb
    import omni.usd
    import omni.kit.app
    from omni.kit.viewport.utility import get_active_viewport
    from omni.kit.viewport.actions.actions import toggle_grid_visibility, toggle_axis_visibility
    from PIL import Image
    import numpy as np
    import press_cp_environment as geometry
    import full_scene_setup as setup
    import display_controller
    from pxr import Usd, UsdGeom, Gf
    from src.generation.value_generator import SequentialValues
    from src.dataset.validate_sync_capture import validate

    config_path = ROOT / "config/dataset_capture.json"
    config = json.loads(config_path.read_text(encoding="utf-8"))
    indices = indices if indices is not None else config["capture"]["verification_indices"]
    carb.settings.get_settings().set("/app/useFabricSceneDelegate", config["capture"]["use_fabric_scene_delegate"])
    cfg = geometry.read_config()
    values = SequentialValues(config["sequence"])
    roi_path = ROOT / "config/slot_crop_comparison.json"
    rois = json.loads(roi_path.read_text(encoding="utf-8"))
    expected_ids = {r["slot_id"] for r in values.frame(0, cfg)["slots"]}
    if {r["id"] for r in rois["slots"]} != expected_ids or len(rois["slots"]) != 42:
        raise ValueError("Crop Slot 연결 불일치")
    resolution = tuple(cfg["camera"]["resolution"])
    for roi in rois["slots"]:
        l,t,r,b = roi["bbox"]
        if not (0 <= l < r <= resolution[0] and 0 <= t < b <= resolution[1]):
            raise ValueError("Crop 경계 이탈")
    sources = [config_path, geometry.CONFIG, roi_path, Path(__file__), Path(display_controller.__file__),
               Path(geometry.__file__), Path(setup.__file__), ROOT / "src/generation/value_generator.py", ROOT / "src/dataset/validate_sync_capture.py"]
    assets = [geometry.SCENE, geometry.ASSET, geometry.ENVIRONMENT, *sorted((geometry.ASSET.parent / "textures").glob("*.png"))]
    original_hashes = {str(p.relative_to(ROOT)): geometry.sha256(p) for p in assets}
    disk = Usd.Stage.Open(str(geometry.SCENE))
    saved_render_settings = str(disk.GetRootLayer().customLayerData.get("renderSettings", {}))
    saved_camera_transform = str(disk.GetPrimAtPath("/World/Cameras/reference").GetAttribute("xformOp:transform").Get())
    def apply_camera(stage):
        with Usd.EditContext(stage, stage.GetSessionLayer()):
            cam = UsdGeom.Camera.Define(stage, "/World/Cameras/reference")
            view = cfg["camera"]["reference"]
            matrix = Gf.Matrix4d().SetLookAt(Gf.Vec3d(*view["position"]), Gf.Vec3d(*view["target"]), Gf.Vec3d(0,0,1)).GetInverse()
            cam.GetPrim().GetAttribute("xformOp:transform").Set(matrix)
            cam.GetHorizontalApertureAttr().Set(36)
            cam.GetVerticalApertureAttr().Set(20.25)
            cam.GetFocalLengthAttr().Set(cfg["camera"]["focal_px"]*36/resolution[0])
    apply_camera(disk)
    geometry.author_render_settings(disk, cfg)
    geometry.validate(disk, cfg)
    del disk
    out = ROOT / "outputs/dataset_sync" / datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S_%fZ")
    out.mkdir(parents=True)
    (out / "frames").mkdir(); (out / "crops").mkdir(); (out / "snapshots").mkdir()
    ctx = omni.usd.get_context()
    viewport = get_active_viewport()
    await asyncio.wait_for(viewport.wait_for_rendered_frames(5), 120)
    ok, error = await ctx.open_stage_async(str(geometry.SCENE))
    if not ok: raise RuntimeError(error)
    stage = ctx.get_stage()
    apply_camera(stage)
    # Kit이 기본값을 생략하므로 메모리에만 Config 렌더 메타데이터를 복원한다.
    geometry.author_render_settings(stage, cfg)
    geometry.validate(stage, cfg)
    applied = setup.apply_render_settings(cfg)
    viewport = get_active_viewport()
    viewport.camera_path = "/World/Cameras/reference"
    viewport.resolution = resolution
    toggle_grid_visibility(viewport, False); toggle_axis_visibility(viewport, False)
    frames = []; labels = []; pixels = []
    for ordinal, index in enumerate(indices):
        frame = values.frame(index, cfg)
        # RC 런타임의 이전 Mesh 잔류를 피하기 위해 프레임마다 불변 USD 스냅샷을 로드한다.
        snapshot_stage = Usd.Stage.Open(str(geometry.SCENE))
        apply_camera(snapshot_stage)
        geometry.author_render_settings(snapshot_stage, cfg)
        checks = display_controller.update(snapshot_stage, cfg, frame)
        snapshot = out / "snapshots" / f"frame_{ordinal:06d}.usda"
        snapshot_stage.Flatten().Export(str(snapshot))
        del snapshot_stage
        ok,error = await ctx.close_stage_async()
        if not ok: raise RuntimeError(error)
        ok,error = await ctx.open_stage_async(str(snapshot))
        if not ok: raise RuntimeError(error)
        stage = ctx.get_stage()
        setup.apply_render_settings(cfg)
        viewport = get_active_viewport()
        viewport.camera_path = "/World/Cameras/reference"
        viewport.resolution = resolution
        toggle_grid_visibility(viewport, False); toggle_axis_visibility(viewport, False)
        path = out / "frames" / f"frame_{ordinal:06d}.png"
        await asyncio.wait_for(viewport.wait_for_rendered_frames(10), 120)
        await setup.capture(viewport, path, resolution)
        for row in checks:
            prim = stage.GetPrimAtPath(row["prim_path"])
            if prim.GetCustomDataByKey("display_text") != row["text"] or display_controller.mesh_signature(stage, row["prim_path"]) != row["mesh_sha256"]:
                raise AssertionError("캡처 중 표시 상태 변경")
        with Image.open(path) as image:
            image.load()
            pixels.append(np.asarray(image.convert("RGB")).copy())
            for roi in rois["slots"]:
                row = next(r for r in checks if r["slot_id"] == roi["id"])
                crop = out / "crops" / f"frame_{ordinal:06d}_{roi['id'].replace('/', '_')}.png"
                image.crop(roi["bbox"]).save(crop)
                labels.append({**row, "image": crop.relative_to(out).as_posix(), "image_sha256": geometry.sha256(crop),
                               "frame_image": path.relative_to(out).as_posix(), "frame_index": index,
                               "frame_id": f"frame_{ordinal:06d}", "run_id": out.name,
                               "bbox": roi["bbox"], "roi_status": "예비 고정 검색창, 정답 bbox 아님", "split": "debug"})
        frames.append({"frame_index": index, "text": values.text_at(index), "image": path.relative_to(out).as_posix(), "sha256": geometry.sha256(path), "snapshot":snapshot.relative_to(out).as_posix(),"snapshot_sha256":geometry.sha256(snapshot), "slots": checks})
        print(f"[CP-DT] CAPTURE {ordinal+1}/{len(indices)} text={values.text_at(index)}", flush=True)
    # 이전 프레임 잔류를 검출: 서로 다른 문자열의 42개 ROI 픽셀이 모두 변해야 한다.
    changes = []
    for n in range(1, len(frames)):
        if frames[n-1]["text"] == frames[n]["text"]: continue
        for roi in rois["slots"]:
            l,t,r,b = roi["bbox"]
            delta = np.abs(pixels[n][t:b,l:r].astype(float) - pixels[n-1][t:b,l:r]).mean()
            if delta < 0.1: raise AssertionError(f"갱신 이미지 변화 부족: {roi['id']} {n} {delta}")
            changes.append({"frame_id": n, "slot_id": roi["id"], "mean_absolute_difference": float(delta)})
    for row in labels:
        path = out / row["image"]
        with Image.open(path) as image:
            image.load()
            l,t,r,b = row["bbox"]
            if image.size != (r-l,b-t) or geometry.sha256(path) != row["image_sha256"]: raise AssertionError("Crop 검증 실패")
    if len({r["image"] for r in labels}) != len(indices)*42: raise AssertionError("중복 이미지 ID")
    if any(geometry.sha256(ROOT / p) != digest for p,digest in original_hashes.items()): raise AssertionError("원본 Asset 변경")
    (out / "labels.jsonl").write_text("".join(json.dumps(row,ensure_ascii=False)+"\n" for row in labels), encoding="utf-8")
    git = lambda *args: subprocess.run(["git",*args],cwd=ROOT,capture_output=True,text=True,check=True).stdout.strip()
    report = {"status":"CAPTURED", "run_id":out.name, "timestamp_utc":datetime.now(timezone.utc).isoformat(),
              "mode":"standalone_headless", "isaac_install_version":Path("C:/isaacsim/VERSION").read_text().strip(),
              "kit_version":omni.kit.app.get_app().get_build_version(), "git_base_commit":git("rev-parse","HEAD"), "git_dirty":bool(git("status","--porcelain")),
              "seed":config["seed"], "config":config, "scene_config":cfg, "roi_config":rois,
              "source_sha256":{str(p.relative_to(ROOT)):geometry.sha256(p) for p in sources}, "asset_sha256":original_hashes,
              "saved_camera_transform":saved_camera_transform,"applied_camera":cfg["camera"],"saved_render_settings":saved_render_settings,"applied_render_settings":applied,"frame_count":len(frames),"crop_count":len(labels),"frames":frames,
              "pixel_change_checks":changes, "labels_sha256":geometry.sha256(out / "labels.jsonl"),
              "limitations":["Mesh·문자열 일치와 렌더 픽셀 변화를 검사. OCR 독립 판독은 미실시", "고정 ROI는 예비 비교 검색창이며 이웃 표시 일부를 포함할 수 있음", "실영상 유사성·최종 학습 데이터 품질 합격을 의미하지 않음"]}
    (out / "report.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    validate(out)
    report["status"] = "PASS"
    (out / "report.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    print(f"[CP-DT] DATASET_SYNC_OK: {out}",flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--indices", type=int, nargs="+")
    args = parser.parse_args()
    from isaacsim import SimulationApp
    app = SimulationApp({"headless":True,"width":1920,"height":1080})
    code = 0
    try:
        app.run_coroutine(run(args.indices))
    except Exception:
        import traceback
        traceback.print_exc(); code = 1
    finally:
        app.close(exit_code=code)
