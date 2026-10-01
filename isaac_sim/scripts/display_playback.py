"""GUI Script Editor/Standalone 공통 연속 표시. 시작할 때 한 번만 Stage 로드."""
import asyncio
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
import time
import math
from collections import deque

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from src.generation.value_generator import SequentialValues
from src.generation.glyph_layout import glyph_layout

_task = None
_stop = False
_controller = None
_prepared = None
_last_status = {"running":False,"index":None,"text":None}


class FabricDisplay:
    def __init__(self, context, cfg):
        from usdrt import Usd as RtUsd, Rt, Gf
        self.context = context
        self.stage_id = context.get_stage_id()
        self.stage = context.get_stage()
        self.rt = RtUsd.Stage.Attach(self.stage_id)
        self.rows = []
        for panel in cfg["panels"]:
            for module in panel["modules"]:
                import press_cp_environment as geometry
                _, w, h = geometry.image_box(cfg, module["bbox"], -.026)
                d = cfg["display"]; vac = module["id"] == "vacuum"
                width = w*d["vacuum_main_width" if vac else "main_width"]
                height = h*d["vacuum_digit_height" if vac else "digit_height"]
                for slot in (1,2):
                    sid = f"{panel['id']}/{module['id']}/slot_{slot}"
                    path = f"/World/Cabinet/Panels/{sid}/Live"
                    attrs={key:Rt.Xformable(self.rt.GetPrimAtPath(f"{path}/{key}")).GetFabricHierarchyLocalMatrixAttr()
                           for key in [*[f"digit_{p}_{c}" for p in range(4) for c in "0123456789"],"decimal"]}
                    if any(not attr.IsValid() for attr in attrs.values()): raise RuntimeError(f"Fabric Transform을 찾을 수 없습니다: {sid}")
                    self.rows.append((sid,path,width,height,attrs))
        if len(self.rows) != 42: raise AssertionError("42 Slot 구성 오류")
        self.index = None; self.text = None
        self.apply_count=0
        self.active={sid:set() for sid,*_ in self.rows}
        self.hidden=Gf.Matrix4d(1).SetTranslate(Gf.Vec3d(1000,1000,1000))

    def apply(self, frame):
        from usdrt import Gf
        if self.context.get_stage_id() != self.stage_id:
            raise RuntimeError("Stage가 변경되어 연속 표시를 종료합니다")
        requested = {r["slot_id"]:r["text"] for r in frame["slots"]}
        if len(frame["slots"]) != 42 or set(requested) != {r[0] for r in self.rows}:
            raise ValueError("Slot 연결 불일치")
        for sid,path,width,height,attrs in self.rows:
            layout=glyph_layout(requested[sid],width,height)
            selected={key for key,_,_ in layout}
            for key in self.active[sid]-selected: attrs[key].Set(self.hidden)
            for key,center,unit in layout:
                matrix=Gf.Matrix4d(1).SetScale(Gf.Vec3d(unit))
                matrix.SetTranslateOnly(Gf.Vec3d(center,0,0))
                attrs[key].Set(matrix)
            self.active[sid]=selected
        self.index = frame["frame_index"]
        self.text = next(iter(requested.values()))
        self.apply_count+=1
        # 정지된 Timeline에서도 숫자 변경 후 RTX/DLSS의 이전 누적 영상을 폐기한다.
        self.context.reset_renderer_accumulation()


def author_live_geometry(stage, cfg):
    """현재 EditTarget에 표시용 Mesh를 한 번 생성한다. 파일 저장은 하지 않는다."""
    from pxr import UsdShade
    import press_cp_environment as geometry
    for panel in cfg["panels"]:
        for module in panel["modules"]:
            for slot in (1, 2):
                path=f"/World/Cabinet/Panels/{panel['id']}/{module['id']}/slot_{slot}"
                for child in list(stage.GetPrimAtPath(path).GetChildren()):
                    if child.GetName() != "Live": child.SetActive(False)
                live=stage.GetPrimAtPath(f"{path}/Live")
                if live: live.SetActive(True)
                on=UsdShade.Material.Get(stage,f"/World/Cabinet/Looks/{'green_led' if slot==1 else 'amber_led'}")
                off=UsdShade.Material.Get(stage,"/World/Cabinet/Looks/off_segment")
                for pos in range(4):
                    for char in "0123456789":
                        geometry.digits(stage,f"{path}/Live/digit_{pos}_{char}",char,[1000,1000,1000],.68,1,on,off)
                geometry.digits(stage,f"{path}/Live/decimal",".",[1000,1000,1000],.24,1,on,off)


async def prepare(config, protect_current=True):
    import carb
    import omni.usd
    from pxr import Usd, UsdGeom, UsdShade, Gf
    import press_cp_environment as geometry
    import full_scene_setup
    from omni.kit.viewport.utility import get_active_viewport
    from omni.kit.viewport.actions.actions import toggle_grid_visibility, toggle_axis_visibility
    cfg = geometry.read_config()
    ctx = omni.usd.get_context()
    current = ctx.get_stage()
    if protect_current and current and any(layer.dirty for layer in current.GetLayerStack(includeSessionLayers=False)):
        raise RuntimeError("현재 Stage를 저장한 뒤 연속 표시를 시작하세요")
    carb.settings.get_settings().set("/app/useFabricSceneDelegate", True)
    stage = Usd.Stage.Open(str(geometry.SCENE))
    with Usd.EditContext(stage, stage.GetSessionLayer()):
        # 별도 실행기는 Timeline Behavior와 동시에 숫자를 제어하지 않는다.
        behavior=stage.GetPrimAtPath("/World/DisplayPlayback")
        if behavior: behavior.SetActive(False)
        author_live_geometry(stage,cfg)
        if config["use_config_camera"]:
            name=config["camera"]; cam=UsdGeom.Camera.Get(stage,f"/World/Cameras/{name}")
            view=cfg["camera"][name]
            cam.GetPrim().GetAttribute("xformOp:transform").Set(Gf.Matrix4d().SetLookAt(Gf.Vec3d(*view["position"]),Gf.Vec3d(*view["target"]),Gf.Vec3d(0,0,1)).GetInverse())
            cam.GetHorizontalApertureAttr().Set(36)
            cam.GetVerticalApertureAttr().Set(20.25)
            cam.GetFocalLengthAttr().Set(cfg["camera"]["focal_px"]*36/cfg["camera"]["resolution"][0] if name=="reference" else view["focal_mm"])
    geometry.author_render_settings(stage,cfg)
    out=ROOT/"outputs/display_playback"/datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S_%fZ")
    out.mkdir(parents=True)
    snapshot=out/"live_scene.usdc"
    stage.Flatten().Export(str(snapshot))
    del stage
    ok,error=await ctx.open_stage_async(str(snapshot))
    if not ok: raise RuntimeError(error)
    full_scene_setup.apply_render_settings(cfg)
    viewport=get_active_viewport()
    viewport.camera_path=f"/World/Cameras/{config['camera']}"
    viewport.resolution=tuple(cfg["camera"]["resolution"])
    toggle_grid_visibility(viewport,False); toggle_axis_visibility(viewport,False)
    await asyncio.wait_for(viewport.wait_for_rendered_frames(10),120)
    return FabricDisplay(ctx,cfg),cfg,out,viewport


def read_config(interval_seconds=None):
    cfg=json.loads((ROOT/"config/display_playback.json").read_text(encoding="utf-8"))
    if interval_seconds is not None: cfg["interval_seconds"]=interval_seconds
    interval=cfg["interval_seconds"]
    if isinstance(interval,bool) or not isinstance(interval,(float,int)) or not math.isfinite(interval) or interval<=0:
        raise ValueError("증가 간격은 유한한 양수 초 단위여야 합니다")
    if cfg["camera"] not in ("reference","overview","detail") or cfg["use_fabric_scene_delegate"] is not True:
        raise ValueError("유효한 카메라와 Fabric Scene Delegate가 필요합니다")
    return cfg


async def run(interval_seconds=None, max_updates=None, start_index=0, protect_current=True):
    global _stop,_controller,_prepared,_last_status
    import omni.kit.app
    config=read_config(interval_seconds)
    _stop=False
    if max_updates is not None and (type(max_updates) is not int or max_updates<=0):
        raise ValueError("max_updates는 양수 정수여야 합니다")
    sequence=json.loads((ROOT/"config/dataset_capture.json").read_text(encoding="utf-8"))
    values=SequentialValues(sequence["sequence"])
    values.text_at(start_index)
    import omni.usd
    if _prepared is not None and _prepared[0].stage_id==omni.usd.get_context().get_stage_id() and _prepared[4]=={k:v for k,v in config.items() if k!="interval_seconds"}:
        controller,cfg,base_out,viewport,_=_prepared
        out=base_out/f"restart_{datetime.now(timezone.utc).strftime('%H%M%S_%f')}"
        out.mkdir()
    else:
        controller,cfg,out,viewport=await prepare(config,protect_current)
        _prepared=(controller,cfg,out,viewport,{k:v for k,v in config.items() if k!="interval_seconds"})
    _controller=controller
    timings=deque(maxlen=1000)
    initial_count=controller.apply_count
    log=(out/"updates.jsonl").open("w",encoding="utf-8")
    try:
        await play(controller,cfg,values,config["interval_seconds"],max_updates,start_index,timings,
                   lambda row:log.write(json.dumps(row,ensure_ascii=False)+"\n"))
    finally:
        log.close()
        _last_status={"running":False,"index":controller.index,"text":controller.text}
        (out/"playback.json").write_text(json.dumps({"status":"STOPPED","updates":controller.apply_count-initial_count,"last_text":controller.text,"last_index":controller.index,"config":config,"sequence":sequence,"recent_timings":list(timings),"updates_log":"updates.jsonl","runtime":"Fabric Transform, 매 갱신 RTX 누적 초기화"},ensure_ascii=False,indent=2),encoding="utf-8")
        _controller=None
    return out


async def play(controller,cfg,values,interval,max_updates,start_index,timings,on_update=None):
    import omni.kit.app
    index=start_index
    applied=0
    while not _stop and (max_updates is None or applied<max_updates):
        started=time.monotonic()
        try: frame=values.frame(index,cfg)
        except IndexError: break
        controller.apply(frame)
        row={"index":index,"text":controller.text,"monotonic_seconds":started}
        timings.append(row)
        if on_update is not None: on_update(row)
        index+=1;applied+=1
        if applied==1 or applied%100==0:
            print(f"[CP-DT] DISPLAY {controller.index}: {controller.text}",flush=True)
        deadline=started+interval
        while not _stop and time.monotonic()<deadline:
            await omni.kit.app.get_app().next_update_async()


async def verify():
    """같은 Stage에서 연속 실행과 실제 영상의 값 복귀를 검증한다."""
    global _stop
    import press_cp_environment as geometry
    import full_scene_setup as setup
    from PIL import Image
    import numpy as np
    import subprocess
    config=read_config()
    sequence=json.loads((ROOT/"config/dataset_capture.json").read_text(encoding="utf-8"))
    values=SequentialValues(sequence["sequence"])
    assets=[geometry.SCENE,geometry.ASSET,geometry.ENVIRONMENT]
    assets.extend(sorted((geometry.ASSET.parent/"textures").glob("*.png")))
    hashes={str(p.relative_to(ROOT)):geometry.sha256(p) for p in assets}
    controller,cfg,out,viewport=await prepare(config,protect_current=False)
    _stop=False; timings=[]
    await play(controller,cfg,values,config["interval_seconds"],20,0,timings)
    if [r["text"] for r in timings]!=[values.text_at(i) for i in range(20)]: raise AssertionError("순차 실행 누락")
    intervals=[b["monotonic_seconds"]-a["monotonic_seconds"] for a,b in zip(timings,timings[1:])]
    if min(intervals)<config["interval_seconds"]*.99: raise AssertionError("갱신 간격 미준수")
    # stop()으로 무제한 루프를 끝내고 다음 값부터 재개할 수 있는지 검사한다.
    stopped=[]
    task=asyncio.ensure_future(play(controller,cfg,values,config["interval_seconds"],None,20,stopped))
    import omni.kit.app
    while len(stopped)<3: await omni.kit.app.get_app().next_update_async()
    stop()
    await task
    last_index=controller.index
    for _ in range(5): await omni.kit.app.get_app().next_update_async()
    if controller.index!=last_index: raise AssertionError("중지 후 값 변경")
    _stop=False; resumed=[]
    await play(controller,cfg,values,config["interval_seconds"],2,last_index+1,resumed)
    if resumed[0]["index"]!=last_index+1: raise AssertionError("재개 인덱스 불일치")
    indices=[0,1,99,100,888,9990,9991]
    pictures=[]; frames=[]
    rois=json.loads((ROOT/"config/slot_crop_comparison.json").read_text(encoding="utf-8"))
    stage_id=controller.stage_id
    for n,index in enumerate(indices):
        controller.apply(values.frame(index,cfg))
        path=out/f"verify_{n:02d}.png"
        await setup.capture(viewport,path,cfg["camera"]["resolution"])
        if controller.context.get_stage_id()!=stage_id: raise AssertionError("실행 중 Stage 재로딩")
        with Image.open(path) as image: pictures.append(np.asarray(image.convert("RGB")).copy())
        # Fabric 실제 숫자 Transform도 생성 조건과 대조한다.
        for sid,root,width,height,attrs in controller.rows:
            layout=glyph_layout(values.text_at(index),width,height)
            for key,center,unit in layout:
                matrix=attrs[key].Get()
                if abs(matrix[3][0]-center)>1e-7 or abs(matrix[0][0]-unit)>1e-7: raise AssertionError(f"Fabric Transform 불일치: {sid}")
        frames.append({"index":index,"text":values.text_at(index),"image":path.name,"sha256":geometry.sha256(path)})
        print(f"[CP-DT] LIVE_VERIFY {index}: {values.text_at(index)}",flush=True)
    checks=[]
    for roi in rois["slots"]:
        l,t,r,b=roi["bbox"]
        same=float(np.abs(pictures[-1][t:b,l:r].astype(float)-pictures[0][t:b,l:r]).mean())
        wrong=float(np.abs(pictures[-1][t:b,l:r].astype(float)-pictures[-2][t:b,l:r]).mean())
        if not same<wrong*.25: raise AssertionError(f"이전 숫자 잔류: {roi['id']} {same} / {wrong}")
        changes=[]
        for n in range(1,len(pictures)):
            delta=float(np.abs(pictures[n][t:b,l:r].astype(float)-pictures[n-1][t:b,l:r]).mean())
            if delta<.1: raise AssertionError(f"화면 변화 누락: {roi['id']}")
            changes.append(delta)
        checks.append({"slot_id":roi["id"],"repeat_difference":same,"previous_difference":wrong,"adjacent_differences":changes})
    if any(geometry.sha256(ROOT/p)!=h for p,h in hashes.items()): raise AssertionError("원본 Asset 변경")
    sheet=Image.new("RGB",(len(frames)*220,42*44+30),"#242424")
    from PIL import ImageDraw
    draw=ImageDraw.Draw(sheet)
    for n,frame in enumerate(frames):
        draw.text((n*220+5,5),frame["text"],fill="white")
        for k,roi in enumerate(rois["slots"]):
            image=Image.fromarray(pictures[n]).crop(roi["bbox"])
            image.thumbnail((205,27),Image.Resampling.NEAREST)
            sheet.paste(image,(n*220+5,30+k*44+14))
            draw.text((n*220+5,30+k*44),roi["id"],fill="white")
    sheet.save(out/"contact_sheet.png")
    git=lambda *args:subprocess.run(["git",*args],cwd=ROOT,capture_output=True,text=True,check=True).stdout.strip()
    sources=[Path(__file__),ROOT/"isaac_sim/scripts/run_display_playback.py",ROOT/"src/generation/glyph_layout.py",ROOT/"src/generation/value_generator.py",ROOT/"config/display_playback.json",ROOT/"config/dataset_capture.json",geometry.CONFIG,Path(geometry.__file__),Path(setup.__file__)]
    report={"status":"PASS","mode":"standalone_headless","isaac_install_version":Path("C:/isaacsim/VERSION").read_text().strip(),"stage_id":stage_id,"stage_reloads_during_updates":0,"config":config,"sequence":sequence,"scene_config":cfg,"seed":None,"git_base_commit":git("rev-parse","HEAD"),"git_dirty":bool(git("status","--porcelain")),"source_sha256":{str(p.relative_to(ROOT)):geometry.sha256(p) for p in sources},"asset_sha256":hashes,"continuous_updates":20,"timings":timings,"stop_resume_checks":{"stopped_at_index":last_index,"stopped_updates":len(stopped),"resumed_updates":resumed},"interval_min":min(intervals),"interval_max":max(intervals),"frames":frames,"roi_checks":checks,"runtime":"Fabric Transform, 매 갱신 RTX 누적 초기화","limitations":["실행 주기는 최소 간격이며 부하가 높으면 지연된다. 값을 건너뛰지 않는다", "전체 9991개 값의 렌더를 저장하지 않음; 값 생성은 전체 순회 테스트", "GUI Script Editor는 공통 실행 경로 제공; 직접 GUI 조작은 별도 확인 필요"]}
    (out/"verification.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    print(f"[CP-DT] DISPLAY_PLAYBACK_OK: {out}",flush=True)
    return out


def start(interval_seconds=None, start_index=0):
    """GUI에서 실행. 이미 실행 중이면 같은 Task를 반환한다."""
    global _task,_stop
    if _task is not None and not _task.done(): return _task
    _stop=False
    _task=asyncio.ensure_future(run(interval_seconds=interval_seconds,start_index=start_index))
    def finished(task):
        if not task.cancelled() and task.exception():
            import traceback
            traceback.print_exception(task.exception())
    _task.add_done_callback(finished)
    return _task


def stop():
    """다음 앱 업데이트에서 중지하며 마지막 표시를 유지한다."""
    global _stop
    _stop=True


def status():
    if _controller is not None:
        return {"running":True,"index":_controller.index,"text":_controller.text}
    return dict(_last_status)
