"""CP 보존, 공장 환경 저장·재열기와 실제 RTX 미리보기 검증."""
import argparse
import asyncio
from datetime import datetime, timezone
import json
from pathlib import Path
import shutil
import subprocess
import sys
import traceback

parser=argparse.ArgumentParser()
parser.add_argument("--reopen-only",action="store_true")
args,_=parser.parse_known_args()

from isaacsim import SimulationApp
app=SimulationApp({"headless":True,"width":1920,"height":1080})


async def run():
    import omni.usd
    from omni.kit.viewport.utility import get_active_viewport
    from omni.kit.viewport.actions.actions import toggle_grid_visibility, toggle_axis_visibility
    from pxr import Usd, UsdGeom
    import factory_environment as factory
    import press_cp_environment as geo
    from full_scene_setup import apply_render_settings, capture

    run_id=datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S_%fZ")
    out=geo.ROOT/"outputs/factory_environment"/run_id
    out.mkdir(parents=True)
    protected=[geo.ASSET,*sorted((geo.ASSET.parent/"textures").glob("*.png")),geo.CONFIG,geo.ROOT/"config/training_capture.json",geo.ROOT/"config/display_playback.json",geo.ROOT/"isaac_sim/scripts/press_cp_play_behavior.py"]
    before_hash={str(p.relative_to(geo.ROOT)):geo.sha256(p) for p in protected}
    def snapshot(stage):
        result={}
        roots=["/World/Cabinet","/World/Lights","/World/DisplayPlayback"]+["/World/Cameras/"+n for n in ["reference","training","overview","detail"]]
        for root in roots:
            assert stage.GetPrimAtPath(root),root
            for prim in Usd.PrimRange(stage.GetPrimAtPath(root)):
                result[str(prim.GetPath())]={"type":prim.GetTypeName(),"custom":str(prim.GetCustomData()),"attrs":{a.GetName():str(a.Get()) for a in prim.GetAttributes()},"rels":{r.GetName():str(r.GetTargets()) for r in prim.GetRelationships()}}
        return result
    def compare_snapshot(stage, expected, label):
        current=snapshot(stage)
        delta={p:{"before":expected.get(p),"after":current.get(p)} for p in set(current)|set(expected) if current.get(p)!=expected.get(p)}
        if delta:
            (out/(label+"_diff.json")).write_text(json.dumps(delta,ensure_ascii=False,indent=2),encoding="utf-8")
            # Kit은 구형 Stage의 렌더 노출을 Camera의 신규 속성으로 변환한다.
            # 이 런타임 변화만 기록·허용하며 파일에는 저장하지 않는다.
            for path,change in delta.items():
                if not path.startswith("/World/Cameras/"):
                    raise AssertionError(f"{label}: 보호 Prim 변경 {path}")
                a,b=change["before"],change["after"]
                assert a and b and all(a[k]==b[k] for k in ["type","custom","rels"])
                changed={k for k in set(a["attrs"])|set(b["attrs"]) if a["attrs"].get(k)!=b["attrs"].get(k)}
                assert all(k.startswith(("exposure:","omni:rtx:autoExposure:")) for k in changed),(path,changed)
        return delta
    before=Usd.Stage.Open(str(geo.SCENE)); before_snapshot=snapshot(before)
    if not args.reopen_only:
        shutil.copy2(geo.SCENE,out/"press_cp_main.before.usda")
        shutil.copy2(geo.ENVIRONMENT,out/"workcell.before.usda")
        cfg=factory.update()
    else:
        cfg=factory.read_config()
    before.Reload()
    assert snapshot(before)==before_snapshot,"CP·기존 Camera·Light·Behavior 변경"
    assert {p:geo.sha256(geo.ROOT/p) for p in before_hash}==before_hash,"보존 파일 Hash 변경"
    written_hash={str(p):geo.sha256(p) for p in [geo.SCENE,geo.ENVIRONMENT]}
    del before
    context=omni.usd.get_context()
    ok,error=await context.open_stage_async(str(geo.SCENE))
    if not ok: raise RuntimeError(error)
    scene_cfg=geo.read_config()
    actual=apply_render_settings(scene_cfg)
    stage=context.get_stage()
    runtime_on_open=compare_snapshot(stage,before_snapshot,"reopen")
    assert UsdGeom.GetStageUpAxis(stage)=="Z" and UsdGeom.GetStageMetersPerUnit(stage)==1
    counts={key:sum(bool(p.GetCustomDataByKey(key)) for p in stage.Traverse()) for key in ["panel_id","module_id","slot_id"]}
    assert list(counts.values())==[7,21,42],counts
    required=["Floor","Building/Roof","Building/BackWall","Structure/Beam_0/Web","LeftPress","RightSkid/Deck","Pipe_0/Handwheel/Rim","LeftMachine/Pipe_0","Walkway/Line_0","Utilities/TraySide_0","CeilingLights/Fixture_0_0/Light"]
    assert all(stage.GetPrimAtPath("/World/Workcell/"+p) for p in required)
    lights=[p for p in Usd.PrimRange(stage.GetPrimAtPath("/World/Workcell/CeilingLights")) if p.GetTypeName()=="RectLight"]
    assert len(lights)==len(cfg["lighting"]["x"])*len(cfg["lighting"]["y"])
    slots=[p for p in stage.Traverse() if p.GetCustomDataByKey("slot_id")]
    assert len({p.GetCustomDataByKey("slot_id") for p in slots})==42
    for prim in stage.Traverse():
        attr=prim.GetAttribute("inputs:file")
        if attr and attr.Get(): assert attr.Get().resolvedPath,str(prim.GetPath())
    viewport=get_active_viewport()
    viewport.resolution=tuple(cfg["preview_resolution"])
    toggle_grid_visibility(viewport,False); toggle_axis_visibility(viewport,False)
    await asyncio.wait_for(viewport.wait_for_rendered_frames(10),120)
    images=[]
    for name in (["factory","reference"] if args.reopen_only else ["factory","workcell","reference","training"]):
        viewport.camera_path="/World/Cameras/"+name
        path=out/(name+".png")
        await capture(viewport,path,cfg["preview_resolution"])
        images.append(path)
        print("[CP-DT] FACTORY_RENDER: "+str(path),flush=True)
    runtime_after_render=compare_snapshot(stage,before_snapshot,"render")
    assert {p:geo.sha256(p) for p in written_hash}==written_hash,"렌더 중 저장 파일 변경"
    assert {p:geo.sha256(geo.ROOT/p) for p in before_hash}==before_hash
    source=[factory.CONFIG,Path(factory.__file__),Path(__file__),Path(geo.__file__)]
    git=lambda *a:subprocess.run(["git",*a],cwd=geo.ROOT,capture_output=True,text=True,check=True).stdout.strip()
    report={"status":"PASS","run_id":run_id,"mode":"standalone_headless","reopen_only":args.reopen_only,"isaac_version":Path("C:/isaacsim/VERSION").read_text().strip(),"usd_version":list(Usd.GetVersion()),"git_base_commit":git("rev-parse","HEAD"),"git_dirty":bool(git("status","--porcelain")),"seed":None,"randomization":False,"config":cfg,"scene_config":scene_cfg,"applied_render_settings":actual,"protected_sha256":before_hash,"protected_prim_count":len(before_snapshot),"checks":{"counts":counts,"cp_and_original_cameras_lights_behavior_unchanged":True,"save_reopen":True,"ceiling_lights":len(lights),"required_structures":required,"textures_resolved":True},"source_sha256":{str(p.relative_to(geo.ROOT)):geo.sha256(p) for p in source},"artifact_sha256":{str(p.relative_to(geo.ROOT)):geo.sha256(p) for p in [geo.SCENE,geo.ENVIRONMENT,*images]},"limitations":["실측 복원 아님: 사진 밖 구조는 가정","정적 시각 모델, 물리 공정·안전 설계 아님","GUI 직접 조작 및 새 조명 아래 학습 데이터/OCR 회귀 미실시"]}
    report["runtime_camera_exposure_migration"]={"on_open":runtime_on_open,"after_render":runtime_after_render,"saved_to_disk":False}
    (out/"verification.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    print("[CP-DT] FACTORY_ENVIRONMENT_OK: "+str(out),flush=True)


exit_code=0
try:
    sys.path.insert(0,str(Path(__file__).resolve().parent))
    app.run_coroutine(run())
except Exception:
    traceback.print_exc(); exit_code=1
finally:
    app.close(exit_code=exit_code)
