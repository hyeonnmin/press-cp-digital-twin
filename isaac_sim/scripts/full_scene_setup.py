"""전체 제어반의 생성, 저장·재열기, 세 시점 렌더 및 검증 기록."""
import asyncio
from datetime import datetime, timezone
import json
from pathlib import Path
import platform
import subprocess
import time

import carb
import omni.kit.app
import omni.usd
from omni.kit.viewport.utility import capture_viewport_to_file, get_active_viewport
from omni.kit.viewport.actions.actions import toggle_grid_visibility, toggle_axis_visibility
from PIL import Image
import numpy as np
from pxr import Usd, Gf

import press_cp_environment as geometry


def apply_render_settings(cfg):
    settings=carb.settings.get_settings()
    actual={}
    for key,value in cfg["rendering"]["settings"].items():
        settings.set(key,value)
        applied=settings.get(key)
        if isinstance(value,list):
            applied=list(applied)
            if any(abs(a-b)>1e-5 for a,b in zip(applied,value)): raise AssertionError(f"렌더 설정 적용 실패: {key}")
        elif isinstance(value,float):
            if abs(applied-value)>1e-5: raise AssertionError(f"렌더 설정 적용 실패: {key}")
        elif applied!=value: raise AssertionError(f"렌더 설정 적용 실패: {key}")
        actual[key]=applied
    return actual


async def capture(viewport,path,resolution):
    app=omni.kit.app.get_app()
    for _ in range(90): await app.next_update_async()
    started=time.time_ns()
    helper=capture_viewport_to_file(viewport,str(path))
    await asyncio.wait_for(helper.wait_for_result(),60)
    deadline=time.monotonic()+20
    while True:
        try:
            if path.stat().st_mtime_ns<started: raise OSError("이전 이미지")
            with Image.open(path) as im:
                if im.size!=tuple(resolution): raise ValueError("잘못된 렌더 해상도")
                im.verify()
            return
        except OSError:
            if time.monotonic()>deadline: raise RuntimeError("PNG 저장 시간 초과")
            await asyncio.sleep(.05)


async def check_led_render(stage,viewport,cfg,out):
    """같은 Scene에서 광학 번짐과 자체 발광을 대조한다. 저장 파일은 변경하지 않는다."""
    settings=carb.settings.get_settings()
    bloom_key="/rtx/post/lensFlares/enabled"
    bloom=settings.get(bloom_key)
    attrs=[stage.GetPrimAtPath(f"/World/Lights/{name}").GetAttribute("inputs:intensity") for name in ("Ambient","key","fill")]
    attrs.extend(stage.GetPrimAtPath(f"/World/Cabinet/Looks/{name}/Surface").GetAttribute("inputs:emissiveColor") for name in ("green_led","amber_led"))
    originals=[attr.Get() for attr in attrs]
    paths=[out/name for name in ("led_bloom_off.png","led_dark_on.png","led_dark_off.png")]
    try:
        settings.set(bloom_key,False)
        await capture(viewport,paths[0],cfg["camera"]["resolution"])
        for attr in attrs[:3]: attr.Set(0.0)
        await capture(viewport,paths[1],cfg["camera"]["resolution"])
        for attr in attrs[3:]: attr.Set(Gf.Vec3f(0,0,0))
        await capture(viewport,paths[2],cfg["camera"]["resolution"])
    finally:
        for attr,value in zip(attrs,originals): attr.Set(value)
        settings.set(bloom_key,bloom)
    crop_config=geometry.ROOT/"config/slot_crop_comparison.json"
    slots=json.loads(crop_config.read_text(encoding="utf-8"))["slots"]
    images=[Image.open(p).convert("RGB") for p in paths[1:]]
    checks=[]
    for slot in slots:
        pixels=[np.asarray(image.crop(slot["bbox"]),dtype=float) for image in images]
        red,green,blue=pixels[0].transpose(2,0,1)
        mask=(red>75)&(green>65)&(np.maximum(red,green)-blue>45)
        mask &= green>=red*.98 if slot["id"].endswith("slot_1") else red>=green*1.08
        if mask.sum()<4: raise AssertionError(f"발광 숫자 픽셀 부족: {slot['id']}")
        # '1'처럼 획이 적은 숫자도 동일한 픽셀 위치끼리 비교한다.
        levels=[float(np.median(rgb.max(axis=2)[mask])) for rgb in pixels]
        delta=levels[0]-levels[1]
        if delta<50: raise AssertionError(f"외부 조명 없는 LED 발광 차이 부족: {slot['id']} {delta}")
        checks.append({"slot_id":slot["id"],"lit_pixels":int(mask.sum()),"on_median":levels[0],"off_median":levels[1],"delta":delta})
    return {"status":"PASS","mode":"환경 조명 0, Bloom 끔, LED Emission 켬/끔 대조; 실제 조도 측정 아님","slots":checks,"crop_config_sha256":geometry.sha256(crop_config)},paths


async def run(rebuild=True,protect_current=True,mode="gui_script_editor",led_checks=False):
    ctx=omni.usd.get_context(); current=ctx.get_stage()
    if protect_current and current and any(l.dirty for l in current.GetLayerStack(includeSessionLayers=False)):
        raise RuntimeError("현재 Stage를 먼저 저장한 뒤 실행하세요.")
    viewport=get_active_viewport()
    if viewport is None: raise RuntimeError("Viewport 없음")
    # 앱 시작 메시지 이후에도 RTX 초기화가 진행될 수 있어 실제 프레임을 기다린다.
    await asyncio.wait_for(viewport.wait_for_rendered_frames(5),120)
    cfg=geometry.build() if rebuild else geometry.read_config()
    disk=Usd.Stage.Open(str(geometry.SCENE)); before=geometry.validate(disk,cfg); del disk
    ok,error=await ctx.open_stage_async(str(geometry.SCENE))
    if not ok: raise RuntimeError(error)
    apply_render_settings(cfg)
    viewport=get_active_viewport()
    if viewport is None: raise RuntimeError("Viewport 없음")
    viewport.camera_path="/World/Cameras/reference"
    viewport.resolution=tuple(cfg["camera"]["resolution"])
    # 본 Scene의 모델에 집중하도록 검토 이미지에서 편집용 격자를 숨긴다.
    toggle_grid_visibility(viewport,False)
    toggle_axis_visibility(viewport,False)
    await asyncio.wait_for(viewport.wait_for_rendered_frames(10),120)
    result=await ctx.save_stage_async()
    if not result[0]: raise RuntimeError(str(result))
    geometry.author_render_settings(ctx.get_stage(),cfg)
    ctx.get_stage().GetRootLayer().Save()
    ok,error=await ctx.close_stage_async()
    if not ok: raise RuntimeError(error)
    for _ in range(10): await omni.kit.app.get_app().next_update_async()
    ok,error=await ctx.open_stage_async(str(geometry.SCENE))
    if not ok: raise RuntimeError(error)
    applied_render_settings=apply_render_settings(cfg)
    after=geometry.validate(ctx.get_stage(),cfg)
    if before!=after: raise AssertionError("저장·재열기 전후 검사 결과가 다름")
    out=geometry.ROOT/"outputs/full_scene";out.mkdir(parents=True,exist_ok=True)
    viewport=get_active_viewport();viewport.resolution=tuple(cfg["camera"]["resolution"])
    toggle_grid_visibility(viewport,False)
    toggle_axis_visibility(viewport,False)
    previews=[]
    for name in (["reference","overview","detail"] if rebuild else ["reference"]):
        viewport.camera_path=f"/World/Cameras/{name}"
        path=out/f"{name}{'' if rebuild else '_reopened'}.png"
        await capture(viewport,path,cfg["camera"]["resolution"]);previews.append(path)
    viewport.camera_path="/World/Cameras/reference"
    led_result=None
    if led_checks:
        diagnostic_out=out/"led_checks"/("build" if rebuild else "reopen")
        diagnostic_out.mkdir(parents=True,exist_ok=True)
        led_result,diagnostic_paths=await check_led_render(ctx.get_stage(),viewport,cfg,diagnostic_out)
        previews.extend(diagnostic_paths)
    git=lambda *args: subprocess.run(["git",*args],cwd=geometry.ROOT,capture_output=True,text=True,check=True).stdout.strip()
    sources=[geometry.CONFIG,Path(geometry.__file__),Path(__file__),geometry.ROOT/"isaac_sim/scripts/cp_label_textures.py",geometry.ROOT/"isaac_sim/scripts/verify_full_scene.py"]
    artifacts=[geometry.ASSET,geometry.ENVIRONMENT,geometry.SCENE,*sorted((geometry.ASSET.parent/"textures").glob("*.png")),*previews]
    report={"status":"PASS","timestamp_utc":datetime.now(timezone.utc).isoformat(),"mode":mode,"rebuilt":rebuild,"isaac_install_version":Path("C:/isaacsim/VERSION").read_text().strip(),"kit_version":omni.kit.app.get_app().get_build_version(),"python":platform.python_version(),"usd_version":list(Usd.GetVersion()),"git_base_commit":git("rev-parse","HEAD"),"git_dirty":bool(git("status","--porcelain")),"source_sha256":{str(p.relative_to(geometry.ROOT)):geometry.sha256(p) for p in sources},"artifact_sha256":{str(p.relative_to(geometry.ROOT)):geometry.sha256(p) for p in artifacts},"checks":after,"config":cfg,"seed":None,"randomization":"없음","limitations":["치수·카메라·광원은 임시 근사값","숫자는 초기 화면 예시이며 검증된 OCR 정답 아님","HMI·안전 안내문은 모식도","동적 값 변경·Dataset 캡처 파이프라인 미검증"]}
    report["applied_render_settings"]=applied_render_settings
    report["led_emissive_slots_checked"]=42
    if led_result is not None: report["led_render_check"]=led_result
    report_path=out/("build_report.json" if rebuild else "reopen_report.json")
    report_path.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    print(f"[CP-DT] FULL_SCENE_OK: {report_path}")
    return report
