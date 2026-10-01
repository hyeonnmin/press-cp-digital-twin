"""숫자 선택 → 명시적 subframe 안정화 → PNG·정답 저장."""
import asyncio
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from src.generation.random_values import RandomValues, slot_ids

_task=None


def read_config(path=None, frames=None, seed=None):
    cfg=json.loads(Path(path or ROOT/"config/training_capture.json").read_text(encoding="utf-8"))
    if frames is not None: cfg["frame_count"]=frames
    if seed is not None: cfg["seed"]=seed
    RandomValues(cfg["seed"],cfg["sampling"])
    for value in [cfg["frame_count"],*cfg["camera"]["resolution"],cfg["render"]["initial_subframes"],
                  cfg["render"]["check_subframes"],cfg["render"]["stable_checks"],cfg["render"]["max_subframes"]]:
        if type(value) is not int or value<=0: raise ValueError("개수와 해상도는 양수 정수여야 합니다")
    r=cfg["render"]
    if r["max_subframes"]<r["initial_subframes"]+r["check_subframes"]*r["stable_checks"]:
        raise ValueError("안정화 최대 subframe 수가 부족합니다")
    if not 0<r["max_roi_mean_difference"]<255: raise ValueError("안정화 오차 범위 오류")
    if not 0<=cfg["camera"]["margin_fraction"]<.5 or cfg["camera"]["distance_m"]<=0:
        raise ValueError("카메라 여백/거리 오류")
    if type(cfg["crop"]["padding_px"]) is not int or cfg["crop"]["padding_px"]<0:
        raise ValueError("Crop 여백 오류")
    if cfg["split"]!="unassigned": raise ValueError("현재는 실험 Split을 확정하지 않습니다")
    return cfg


async def run(config_path=None, frames=None, seed=None, protect_current=True, output_root=None):
    import carb
    import omni.usd
    import omni.timeline
    import omni.kit.app
    import omni.replicator.core as rep
    from pxr import Usd, UsdGeom, Sdf
    from PIL import Image, ImageDraw
    import numpy as np
    import press_cp_environment as geometry
    import display_playback
    import training_camera
    import full_scene_setup

    cfg=read_config(config_path,frames,seed)
    scene=geometry.read_config()
    ctx=omni.usd.get_context()
    current=ctx.get_stage()
    if protect_current and current and any(l.dirty for l in current.GetLayerStack(includeSessionLayers=False)):
        raise RuntimeError("미저장 Stage를 먼저 저장한 뒤 학습용 생성을 시작하세요")
    destination=Path(output_root) if output_root is not None else ROOT/"datasets/synthetic/cp_training"
    if not destination.is_absolute(): destination=ROOT/destination
    out=destination.resolve()/datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S_%fZ")
    for folder in ("frames","crops","verification"): (out/folder).mkdir(parents=True,exist_ok=False)
    assets=[geometry.SCENE,geometry.ASSET,geometry.ENVIRONMENT,*sorted((geometry.ASSET.parent/"textures").glob("*.png"))]
    sources=[Path(__file__),Path(training_camera.__file__),Path(display_playback.__file__),Path(geometry.__file__),
             Path(full_scene_setup.__file__),ROOT/"isaac_sim/scripts/generate_training_data.py",
             ROOT/"src/generation/random_values.py",ROOT/"src/generation/glyph_layout.py",ROOT/"src/dataset/validate_training_capture.py",
             ROOT/"config/training_capture.json",geometry.CONFIG]
    git=lambda *args:subprocess.run(["git",*args],cwd=ROOT,capture_output=True,text=True,check=True).stdout.strip()
    report={"schema_version":1,"status":"RUNNING","run_id":out.name,"config":cfg,"scene_config":scene,
            "seed":cfg["seed"],"split":cfg["split"],"git_base_commit":git("rev-parse","HEAD"),"git_dirty":bool(git("status","--porcelain")),
            "source_sha256":{p.relative_to(ROOT).as_posix():geometry.sha256(p) for p in sources},
            "asset_sha256":{p.relative_to(ROOT).as_posix():geometry.sha256(p) for p in assets},
            "isaac_install_version":Path("C:/isaacsim/VERSION").read_text().strip(),
            "kit_version":omni.kit.app.get_app().get_build_version(),"frame_count":0,"crop_count":0,
            "limitations":["정면 직교 카메라는 실측 카메라 복원이 아님","독립 OCR 모델 판독·Real Test 평가는 미실시",
                            "이미지 품질·안정화 검증은 최종 학습 효과를 보장하지 않음","Split은 unassigned; 프레임 단위 분리 필요"]}
    manifest=out/"manifest.json"
    def save_report(): manifest.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    save_report()
    rp=annotator=None
    try:
        omni.timeline.get_timeline_interface().stop()
        display_playback.stop()
        settings=carb.settings.get_settings()
        settings.set("/app/useFabricSceneDelegate",True)
        rep.orchestrator.set_capture_on_play(False)
        stage=Usd.Stage.Open(str(geometry.SCENE))
        with Usd.EditContext(stage,stage.GetSessionLayer()):
            # 중앙 경계는 숨겨 둘 숫자 변형을 추가하기 전에 계산한다.
            camera=training_camera.configure(stage,cfg["camera"])
            stage.GetPrimAtPath("/World/DisplayPlayback").SetActive(False)
            display_playback.author_live_geometry(stage,scene)
        camera_stage=Usd.Stage.CreateNew(str(out/"training_camera.usda"))
        UsdGeom.Xform.Define(camera_stage,"/World")
        UsdGeom.Scope.Define(camera_stage,"/World/Cameras")
        Sdf.CopySpec(stage.GetSessionLayer(),cfg["camera"]["path"],camera_stage.GetRootLayer(),cfg["camera"]["path"])
        camera_stage.GetRootLayer().Save()
        flat=Usd.Stage.Open(stage.Flatten())
        flat.RemovePrim("/Render")  # 저장된 GUI RenderProduct의 설정을 새 캡처에 상속하지 않는다.
        flat.GetRootLayer().Export(str(out/"capture_scene.usdc"))
        del flat,stage
        ok,error=await ctx.open_stage_async(str(out/"capture_scene.usdc"))
        if not ok: raise RuntimeError(error)
        stage=ctx.get_stage()
        stage_id=ctx.get_stage_id()
        report["camera"]=camera
        report["panel_regions"]=training_camera.panel_regions(stage,camera,scene)
        report["applied_render_settings"]=full_scene_setup.apply_render_settings(scene)
        for key,value in cfg["render"]["settings"].items():
            settings.set(key,value)
            actual=settings.get(key)
            if actual!=value: raise AssertionError(f"렌더 설정 적용 실패: {key} {actual}")
            report["applied_render_settings"][key]=actual
        from omni.kit.viewport.utility import get_active_viewport
        viewport=get_active_viewport()
        if viewport: viewport.camera_path=cfg["camera"]["path"]
        rp=rep.create.render_product(cfg["camera"]["path"],tuple(cfg["camera"]["resolution"]),name="CPTraining")
        annotator=rep.AnnotatorRegistry.get_annotator("rgb")
        annotator.attach(rp)

        async def render(count):
            await asyncio.wait_for(rep.orchestrator.step_async(delta_time=0.0,rt_subframes=count,pause_timeline=True,wait_for_render=True),180)
            pixels=np.asarray(annotator.get_data()).copy()
            w,h=cfg["camera"]["resolution"]
            if pixels.shape!=(h,w,4) or pixels.dtype!=np.uint8:
                raise AssertionError(f"RGB Annotator 해상도/형식 오류: {pixels.shape}, {pixels.dtype}")
            return pixels[:,:,:3].copy()

        await render(cfg["render"]["initial_subframes"])
        for key,expected in cfg["render"]["settings"].items():
            if settings.get(key)!=expected: raise AssertionError(f"Replicator 초기화 후 렌더 설정 변경: {key}")
        controller=display_playback.FabricDisplay(ctx,scene)

        async def capture(frame):
            with Usd.EditContext(stage,stage.GetSessionLayer()):
                for row in frame["slots"]:
                    stage.GetPrimAtPath(f"/World/Cabinet/Panels/{row['slot_id']}").SetCustomDataByKey("display_text",row["text"])
            controller.apply(frame)
            rows=training_camera.regions(controller,camera,frame,cfg["crop"]["padding_px"])
            if min(r["digit_height_px"] for r in rows)<cfg["crop"]["minimum_digit_height_px"]:
                raise AssertionError("숫자 픽셀 높이가 부족합니다")
            settings=cfg["render"]
            count=settings["initial_subframes"]
            previous=await render(count)
            stable=0
            checks=[]
            while count+settings["check_subframes"]<=settings["max_subframes"]:
                pixels=await render(settings["check_subframes"])
                count+=settings["check_subframes"]
                diffs=[]
                for row in rows:
                    l,t,r,b=row["slot_roi"]
                    diffs.append(float(np.abs(pixels[t:b,l:r].astype(float)-previous[t:b,l:r]).mean()))
                maximum=max(diffs)
                stable=stable+1 if maximum<=settings["max_roi_mean_difference"] else 0
                checks.append({"subframes":count,"maximum_slot_mean_difference":maximum})
                if stable>=settings["stable_checks"]: break
                previous=pixels
            else: raise AssertionError(f"렌더 안정화 실패: {checks}")
            after=training_camera.regions(controller,camera,frame,cfg["crop"]["padding_px"])
            if rows!=after or controller.index!=frame["frame_index"] or ctx.get_stage_id()!=stage_id:
                raise AssertionError("캡처 중 숫자/Stage 변경")
            for row in rows:
                if stage.GetPrimAtPath(f"/World/Cabinet/Panels/{row['slot_id']}").GetCustomDataByKey("display_text")!=row["text"]:
                    raise AssertionError("표시 문자열 불일치")
            return pixels,rows,{"subframes":count,"checks":checks,"consecutive_passes":stable}

        # 데이터와 분리된 렌더 검증: 0.0 → 999.0 → 0.0 잔류 검사.
        probes=[]
        probe_arrays=[]
        for n,text in enumerate(cfg["verification"]["probe_values"]):
            frame={"frame_index":n,"slots":[{"slot_id":sid,"text":text} for sid in slot_ids(scene)]}
            pixels,rows,settle=await capture(frame)
            name=f"verification/probe_{n}.png"
            Image.fromarray(pixels).save(out/name)
            probe_arrays.append(pixels)
            probes.append({"text":text,"image":name,"sha256":geometry.sha256(out/name),"settle":settle})
            print(f"[CP-DT] TRAINING_PROBE {text}, subframes={settle['subframes']}",flush=True)
        if cfg["verification"]["probe_values"]!=["0.0","999.0","0.0"]: raise ValueError("검증 문자열 순서 오류")
        repeats=[]
        for row in rows:
            l,t,r,b=row["slot_roi"]
            same=float(np.abs(probe_arrays[2][t:b,l:r].astype(float)-probe_arrays[0][t:b,l:r]).mean())
            wrong=float(np.abs(probe_arrays[2][t:b,l:r].astype(float)-probe_arrays[1][t:b,l:r]).mean())
            if wrong<.1 or same>=wrong*cfg["verification"]["maximum_repeat_ratio"]:
                raise AssertionError(f"이전 숫자 잔류/영상 변화 누락: {row['slot_id']}, {same}/{wrong}")
            repeats.append({"slot_id":row["slot_id"],"slot_roi":row["slot_roi"],"repeat_difference":same,"previous_difference":wrong})
        report["verification"]={"probes":probes,"repeat_checks":repeats}
        del probe_arrays
        generator=RandomValues(cfg["seed"],cfg["sampling"])
        with (out/"frames.jsonl").open("w",encoding="utf-8") as frame_log,(out/"labels.jsonl").open("w",encoding="utf-8") as label_log:
            for index in range(cfg["frame_count"]):
                frame=generator.frame(index,scene)
                pixels,rows,settle=await capture(frame)
                fid=f"frame_{index:06d}"
                frame_path=f"frames/{fid}.png"
                image=Image.fromarray(pixels)
                image.save(out/frame_path)
                records=[]
                for row in rows:
                    crop_path=f"crops/{fid}_{row['slot_id'].replace('/','_')}.png"
                    image.crop(row["bbox"]).save(out/crop_path)
                    record={**row,"image":crop_path,"sha256":geometry.sha256(out/crop_path),"frame_image":frame_path,
                            "frame_id":fid,"frame_index":index,"run_id":out.name,"split":cfg["split"]}
                    records.append(record)
                entry={**frame,"frame_id":fid,"image":frame_path,"sha256":geometry.sha256(out/frame_path),"settle":settle}
                # 파일 완료 후에만 해당 프레임의 연결 정보를 기록한다.
                frame_log.write(json.dumps(entry,ensure_ascii=False)+"\n");frame_log.flush()
                label_log.write("".join(json.dumps(r,ensure_ascii=False)+"\n" for r in records));label_log.flush()
                report["frame_count"]+=1;report["crop_count"]+=len(records)
                save_report()
                if index==0:
                    preview=image.copy()
                    draw=ImageDraw.Draw(preview)
                    for row in rows: draw.rectangle(row["bbox"],outline="red",width=2)
                    preview.thumbnail((1920,1080));preview.save(out/"camera_preview.png")
                    sheet=Image.new("RGB",(3*360,14*90),"#222222")
                    draw=ImageDraw.Draw(sheet)
                    for n,row in enumerate(rows):
                        x=(n//14)*360;y=(n%14)*90
                        draw.text((x+6,y+4),f"{row['slot_id']}  GT={row['text']}",fill="white")
                        crop=image.crop(row["bbox"])
                        scale=min(3,345/crop.width,60/crop.height)
                        crop=crop.resize((int(crop.width*scale),int(crop.height*scale)),Image.Resampling.NEAREST)
                        sheet.paste(crop,(x+6,y+24))
                    sheet.save(out/"contact_sheet.png")
                print(f"[CP-DT] TRAINING_FRAME {index+1}/{cfg['frame_count']}, subframes={settle['subframes']}",flush=True)
        if any(geometry.sha256(ROOT/p)!=h for p,h in report["asset_sha256"].items()):
            raise AssertionError("원본 Scene/Asset 변경")
        report["labels_sha256"]=geometry.sha256(out/"labels.jsonl")
        report["frames_sha256"]=geometry.sha256(out/"frames.jsonl")
        report["status"]="GENERATED"
        save_report()
        from src.dataset.validate_training_capture import validate
        validate(out)
        report["status"]="PASS"
        save_report()
        print(f"[CP-DT] TRAINING_DATA_OK: {out}",flush=True)
        return out
    except BaseException as exc:
        report["status"]="FAILED";report["error"]=str(exc);save_report()
        raise
    finally:
        if annotator is not None: annotator.detach()
        if rp is not None: rp.destroy()


def start(frames=None,seed=None):
    """GUI Script Editor에서 실행. 중복 작업을 만들지 않는다."""
    global _task
    if _task is not None and not _task.done(): return _task
    _task=asyncio.ensure_future(run(frames=frames,seed=seed))
    return _task
