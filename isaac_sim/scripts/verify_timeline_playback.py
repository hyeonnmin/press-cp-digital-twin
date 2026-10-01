"""저장된 USD에서 Behavior를 자동 로드하고 실제 Timeline 이벤트를 검사한다."""
import asyncio
from datetime import datetime, timezone
import json
import time


async def verify():
    import carb
    import carb.eventdispatcher
    import omni.kit.app
    import omni.usd
    import omni.timeline
    import omni.behavior.scripting.core as scripting
    import omni.behavior.scripting.core.scripts.script_manager as manager_module
    import traceback
    # Kit 로더가 내부 프레임의 예외 메시지를 생략하므로 검증 로그에는 전문을 남긴다.
    manager_module.traceback_format_exception=lambda *args,**kwargs: traceback.print_exc()
    from omni.kit.viewport.utility import get_active_viewport
    from pxr import Usd, UsdGeom, Gf, Sdf
    import press_cp_environment as geometry
    import full_scene_setup as setup
    import numpy as np
    from PIL import Image

    app=omni.kit.app.get_app()
    ctx=omni.usd.get_context()
    timeline=omni.timeline.get_timeline_interface()
    loaded=[]
    def on_loaded(event):
        if str(event.payload["prim_path"])=="/World/DisplayPlayback":
            loaded.append(event.payload["script_instance"])
    observer=carb.eventdispatcher.get_eventdispatcher().observe_event(
        event_name=scripting.GLOBAL_EVENT_SCRIPT_LOADED,on_event=on_loaded)
    cfg=geometry.read_config()
    out=geometry.ROOT/"outputs/timeline_playback"/datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S_%fZ")
    out.mkdir(parents=True)
    hashes={str(p.relative_to(geometry.ROOT)):geometry.sha256(p) for p in (geometry.SCENE,geometry.ASSET,geometry.ENVIRONMENT)}
    settings=carb.settings.get_settings()
    previous=settings.get("/app/scripting/ignoreWarningDialog")
    # 이 검증 프로세스에서만 방금 작성한 로컬 Scene의 실행을 허용한다.
    settings.set("/app/scripting/ignoreWarningDialog",True)
    try:
        ok,error=await ctx.open_stage_async(str(geometry.SCENE))
        if not ok: raise RuntimeError(error)
        async def until(predicate):
            deadline=time.monotonic()+120
            while not predicate():
                if loaded and loaded[0].error: raise RuntimeError(loaded[0].error)
                if time.monotonic()>deadline: raise TimeoutError("Timeline 검증 대기 시간 초과")
                await app.next_update_async()
        await until(lambda:len(loaded)==1)
    finally:
        settings.set("/app/scripting/ignoreWarningDialog",previous)
    behavior=loaded[0]
    stage=ctx.get_stage()
    stage_id=ctx.get_stage_id()
    root_before=stage.GetRootLayer().ExportToString()
    viewport=get_active_viewport()
    # 영상 비교의 기존 ROI에 맞춘 검증 전용 카메라; Behavior 자체는 카메라를 건드리지 않는다.
    with Usd.EditContext(stage,stage.GetSessionLayer()):
        view=cfg["camera"]["reference"]
        cam=UsdGeom.Camera.Get(stage,"/World/Cameras/reference")
        cam.GetPrim().GetAttribute("xformOp:transform").Set(Gf.Matrix4d().SetLookAt(Gf.Vec3d(*view["position"]),Gf.Vec3d(*view["target"]),Gf.Vec3d(0,0,1)).GetInverse())
        cam.GetHorizontalApertureAttr().Set(36)
        cam.GetVerticalApertureAttr().Set(20.25)
        cam.GetFocalLengthAttr().Set(cfg["camera"]["focal_px"]*36/cfg["camera"]["resolution"][0])
    setup.apply_render_settings(cfg)
    viewport.camera_path="/World/Cameras/reference"
    viewport.resolution=tuple(cfg["camera"]["resolution"])
    camera_before=str(cam.GetPrim().GetAttribute("xformOp:transform").Get())
    for _ in range(5): await app.next_update_async()
    root_before=stage.GetRootLayer().ExportToString()
    timeline.play()
    await until(lambda:behavior.controller is not None)
    timeline.pause()
    for _ in range(3): await app.next_update_async()
    assert behavior.controller.index==0
    pictures=[]
    async def capture(name):
        path=out/f"{name}.png"
        index=behavior.controller.index
        await setup.capture(viewport,path,cfg["camera"]["resolution"])
        assert behavior.controller.index==index,"Pause/Stop 후 값 변경"
        for sid,*_ in behavior.controller.rows:
            assert stage.GetPrimAtPath(f"/World/Cabinet/Panels/{sid}").GetCustomDataByKey("display_text")==behavior.controller.text
        with Image.open(path) as im: pictures.append(np.array(im.convert("RGB")))
    await capture("initial_0")
    timeline.play()
    transitions=[]
    last=0
    while behavior.controller.index<20:
        await app.next_update_async()
        index=behavior.controller.index
        if index!=last:
            assert index==last+1,"값 건너뛰기"
            transitions.append({"index":index,"text":behavior.controller.text,"time":behavior.last_update_time})
            last=index
    timeline.pause()
    for _ in range(3): await app.next_update_async()
    paused=behavior.controller.index
    await capture("paused_value")
    timeline.play()
    await until(lambda:behavior.controller.index>paused)
    assert behavior.controller.index==paused+1
    timeline.stop()
    for _ in range(5): await app.next_update_async()
    assert behavior.controller.index==0
    await capture("stopped_0")
    # 경계 앞에서 시작해 두 번의 실제 Timeline 갱신으로 최대값·순환 확인.
    behavior._next_index=9990
    timeline.play()
    await until(lambda:behavior.controller.index==9990)
    assert behavior.controller.text=="999.0"
    timeline.pause()
    for _ in range(3): await app.next_update_async()
    await capture("maximum_999")
    timeline.play()
    await until(lambda:behavior.controller.index==9991)
    assert behavior.controller.text=="0.0"
    timeline.pause()
    for _ in range(3): await app.next_update_async()
    await capture("wrapped_0")
    timeline.stop()
    for _ in range(3): await app.next_update_async()
    timeline.play()
    await until(lambda:behavior.controller.index==1)
    timeline.stop()
    for _ in range(3): await app.next_update_async()
    assert behavior.controller.index==0
    assert ctx.get_stage_id()==stage_id
    root_after=stage.GetRootLayer().ExportToString()
    if root_before!=root_after:
        import difflib
        (out/"root_runtime_diff.txt").write_text("".join(difflib.unified_diff(root_before.splitlines(True),root_after.splitlines(True))),encoding="utf-8")
    def without_kit_defaults(content):
        layer=Sdf.Layer.CreateAnonymous()
        layer.ImportFromString(content)
        copy=Usd.Stage.Open(layer)
        # 실제 관찰된 Kit 자동 생성 항목만 비교에서 제외한다. 디스크 저장은 하지 않는다.
        copy.RemovePrim("/PhysicsScene")
        for prim in copy.Traverse():
            prim.RemoveProperty("omni:rtx:rt:ecoMode:enabled")
        return layer.ExportToString()
    assert without_kit_defaults(root_before)==without_kit_defaults(root_after),"숫자 동작이 원본 레이어를 수정함"
    assert camera_before==str(cam.GetPrim().GetAttribute("xformOp:transform").Get())
    assert all(geometry.sha256(geometry.ROOT/p)==digest for p,digest in hashes.items())
    rois=json.loads((geometry.ROOT/"config/slot_crop_comparison.json").read_text(encoding="utf-8"))
    checks=[]
    for roi in rois["slots"]:
        l,t,r,b=roi["bbox"]
        repeat=float(np.abs(pictures[2][t:b,l:r].astype(float)-pictures[0][t:b,l:r]).mean())
        changed=float(np.abs(pictures[1][t:b,l:r].astype(float)-pictures[0][t:b,l:r]).mean())
        wrapped=float(np.abs(pictures[4][t:b,l:r].astype(float)-pictures[0][t:b,l:r]).mean())
        maximum=float(np.abs(pictures[3][t:b,l:r].astype(float)-pictures[0][t:b,l:r]).mean())
        assert changed>.1 and max(repeat,wrapped)<maximum*.25,(roi["id"],repeat,wrapped,maximum)
        checks.append({"slot_id":roi["id"],"repeat_difference":repeat,"changed_difference":changed,"wrapped_difference":wrapped,"maximum_difference":maximum})
    intervals=[b["time"]-a["time"] for a,b in zip(transitions,transitions[1:])]
    assert min(intervals)>=behavior.config["interval_seconds"]*.99
    report={"status":"PASS","mode":"USD attached Behavior, headless Timeline Play/Pause/Stop",
            "stage_id":stage_id,"asset_sha256":hashes,"config":behavior.config,
            "sequence":behavior.values.config if hasattr(behavior.values,"config") else json.loads((geometry.ROOT/"config/dataset_capture.json").read_text(encoding="utf-8")),
            "transitions":transitions,"pause_index":paused,"stop_index":0,"wrap":["999.0","0.0"],
            "roi_checks":checks,"interval_min":min(intervals),"interval_max":max(intervals),
            "limitations":["GUI 버튼 직접 클릭과 스크립트 허용 창은 미검증","전체 범위 렌더는 하지 않음"]}
    import subprocess
    report["git_base_commit"]=subprocess.run(["git","rev-parse","HEAD"],cwd=geometry.ROOT,capture_output=True,text=True,check=True).stdout.strip()
    report["git_dirty"]=bool(subprocess.run(["git","status","--porcelain"],cwd=geometry.ROOT,capture_output=True,text=True,check=True).stdout.strip())
    report["isaac_install_version"]=__import__("pathlib").Path("C:/isaacsim/VERSION").read_text().strip()
    report["seed"]=None
    report["scene_config"]=cfg
    report["source_sha256"]={str(p.relative_to(geometry.ROOT)):geometry.sha256(p) for p in (
        geometry.ROOT/"isaac_sim/scripts/press_cp_play_behavior.py",geometry.ROOT/"isaac_sim/scripts/timeline_display.py",
        geometry.ROOT/"isaac_sim/scripts/display_playback.py",geometry.ROOT/"isaac_sim/scripts/verify_timeline_playback.py",
        geometry.ROOT/"src/generation/value_generator.py",geometry.ROOT/"src/generation/glyph_layout.py",geometry.CONFIG)}
    report["kit_runtime_layer_additions"]=["/PhysicsScene","omni:rtx:rt:ecoMode:enabled (미저장)"]
    (out/"verification.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    observer=None
    await ctx.close_stage_async()
    print(f"[CP-DT] TIMELINE_PLAYBACK_OK: {out}",flush=True)
    return out
