"""Script Editor: 이 모듈의 run()을 asyncio.ensure_future로 실행한다."""

import asyncio
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import platform
import subprocess
import time

import omni.kit.app
import omni.usd
from omni.kit.viewport.utility import capture_viewport_to_file, get_active_viewport
from pxr import Usd
from PIL import Image

import panel_1_geometry as geometry


async def run(execution_mode="gui_script_editor", rebuild=True, protect_current=True):
    context = omni.usd.get_context()
    current = context.get_stage()
    if protect_current and current and any(layer.dirty for layer in current.GetLayerStack(includeSessionLayers=False)):
        raise RuntimeError("현재 Stage에 미저장 변경이 있습니다. 먼저 저장한 뒤 실행하세요.")
    cfg = geometry.build() if rebuild else geometry.read_config()
    # 먼저 디스크에서 별도로 열어 파일과 상대 참조를 검사한다.
    disk_stage = Usd.Stage.Open(str(geometry.SCENE))
    disk_check = geometry.validate(disk_stage)
    del disk_stage
    ok, error = await context.open_stage_async(str(geometry.SCENE))
    if not ok:
        raise RuntimeError(f"Stage 열기 실패: {error}")
    open_check = geometry.validate(context.get_stage())
    viewport = get_active_viewport()
    if viewport is None:
        raise RuntimeError("검증용 Viewport가 없습니다.")
    viewport.camera_path = "/World/ReviewCamera"
    viewport.resolution = tuple(cfg["preview"]["resolution"])
    saved = await context.save_stage_async()
    if not saved[0]:
        raise RuntimeError(f"Stage 저장 실패: {saved[1]}")
    ok, error = await context.close_stage_async()
    if not ok:
        raise RuntimeError(f"Stage 닫기 실패: {error}")
    ok, error = await context.open_stage_async(str(geometry.SCENE))
    if not ok:
        raise RuntimeError(f"Stage 재열기 실패: {error}")
    reopened_check = geometry.validate(context.get_stage())
    if disk_check != open_check or open_check != reopened_check:
        raise AssertionError("저장·재열기 전후 Geometry 검사 결과가 다릅니다.")

    output = geometry.ROOT / "outputs/phase2_validation"
    output.mkdir(parents=True, exist_ok=True)
    viewport = get_active_viewport()
    if viewport is None:
        raise RuntimeError("검증용 Viewport가 없습니다.")
    viewport.camera_path = "/World/ReviewCamera"
    viewport.resolution = tuple(cfg["preview"]["resolution"])
    app = omni.kit.app.get_app()
    for _ in range(60):
        await app.next_update_async()
    preview_path = output / ("panel_1_preview.png" if rebuild else "panel_1_reopened.png")
    capture_started = time.time_ns()
    capture = capture_viewport_to_file(viewport, str(preview_path))
    await asyncio.wait_for(capture.wait_for_result(), timeout=60)
    # Capture future는 이미지 인코더의 파일 기록보다 먼저 완료될 수 있다.
    deadline = time.monotonic() + 15
    while True:
        try:
            if preview_path.stat().st_mtime_ns < capture_started:
                raise OSError("이전 실행의 이미지입니다.")
            with Image.open(preview_path) as rendered:
                if rendered.size != tuple(cfg["preview"]["resolution"]):
                    raise ValueError("렌더 해상도가 Config와 다릅니다.")
                rendered.verify()
            break
        except OSError:
            if time.monotonic() >= deadline:
                raise RuntimeError("렌더 이미지 기록이 완료되지 않았습니다.")
            await asyncio.sleep(0.05)

    git_commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=geometry.ROOT, capture_output=True, text=True, check=True).stdout.strip()
    git_dirty = bool(subprocess.run(["git", "status", "--porcelain"], cwd=geometry.ROOT, capture_output=True, text=True, check=True).stdout.strip())
    isaac_version_file = Path(os.environ.get("ISAAC_PATH", "C:/isaacsim")) / "VERSION"
    report = {
        "status": "PASS",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "execution_mode": execution_mode,
        "rebuilt": rebuild,
        "isaac_install_version": isaac_version_file.read_text().strip(),
        "kit_version": app.get_build_version(),
        "python_version": platform.python_version(),
        "usd_version": list(Usd.GetVersion()),
        "git_base_commit": git_commit,
        "git_worktree_dirty": git_dirty,
        "source_sha256": {str(p.relative_to(geometry.ROOT)): geometry.sha256(p) for p in [geometry.CONFIG, Path(geometry.__file__), Path(__file__), geometry.ROOT / "isaac_sim/scripts/verify_panel_1_standalone.py"]},
        "artifact_sha256": {str(p.relative_to(geometry.ROOT)): geometry.sha256(p) for p in [geometry.ASSET, geometry.SCENE, preview_path]},
        "video_reference": cfg["reference"],
        "seed": None,
        "randomization": "없음; 고정 Geometry 검증",
        "checks": {"disk_open": disk_check, "context_open": open_check, "save_close_reopen": reopened_check},
        "applied_config": cfg,
        "limitations": ["실측 치수 아님", "숫자 미구현", "영상 유사성 및 실제 카메라 보정 미검증", "Dataset 아님"],
    }
    report_path = output / ("build_report.json" if rebuild else "reopen_report.json")
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[CP-DT] PANEL1_GEOMETRY_OK: {report_path}")
    return report
