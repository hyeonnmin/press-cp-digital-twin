"""완료된 CP Run을 Panel 이미지와 YOLO Slot 검출 라벨로 변환한다."""
import argparse
from collections import defaultdict
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import random
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
MODULES=("temperature","pressure","vacuum")
SLOTS=tuple(f"{m}/slot_{s}" for m in MODULES for s in (1,2))


def digest(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read_config(path=None, class_mode=None):
    cfg=json.loads(Path(path or ROOT/"config/panel_detection.json").read_text(encoding="utf-8"))
    if class_mode is not None: cfg["class_mode"]=class_mode
    if cfg["class_mode"] not in ("single","six_slots"): raise ValueError("class_mode 오류")
    if cfg["bbox_source"] not in ("bbox","digit_bbox","slot_roi"): raise ValueError("bbox_source 오류")
    if type(cfg["panel_padding_px"]) is not int or cfg["panel_padding_px"]<0: raise ValueError("Panel 여백 오류")
    if type(cfg["split_seed"]) is not int: raise ValueError("split_seed는 정수여야 합니다")
    if not 0<cfg["validation_fraction"]<1: raise ValueError("validation_fraction 범위 오류")
    return cfg


def frame_split(frame_ids, seed, fraction):
    ids=sorted(frame_ids)
    if len(ids)<2 or len(ids)!=len(set(ids)): raise ValueError("분할에는 서로 다른 원본 프레임이 최소 2개 필요합니다")
    if not 0<fraction<1: raise ValueError("분할 비율 오류")
    random.Random(seed).shuffle(ids)
    count=max(1,min(len(ids)-1,round(len(ids)*fraction)))
    validation=set(ids[:count])
    return {fid:"val" if fid in validation else "train" for fid in ids}


def local_box(box, panel_box):
    l,t,r,b=box
    pl,pt,pr,pb=panel_box
    if not all(math.isfinite(v) for v in (*box,*panel_box)) or not (pl<=l<r<=pr and pt<=t<b<=pb):
        raise ValueError(f"Slot bbox가 Panel 밖으로 잘립니다: {box} / {panel_box}")
    return [l-pl,t-pt,r-pl,b-pt]


def normalized_box(box, width, height):
    l,t,r,b=box
    if not (0<=l<r<=width and 0<=t<b<=height): raise ValueError("정규화할 bbox 경계 오류")
    return [(l+r)/(2*width),(t+b)/(2*height),(r-l)/width,(b-t)/height]


def _project_box(bounds, camera, padding=0):
    l,b,r,t=bounds  # world X/Z min/max
    cx,_,cz=camera["target"]
    w,h=camera["resolution"]
    sx=w/camera["span_x"]; sy=h/camera["span_z"]
    box=[math.floor((l-cx)*sx+w/2)-padding,math.floor(h/2-(t-cz)*sy)-padding,
         math.ceil((r-cx)*sx+w/2)+padding,math.ceil(h/2-(b-cz)*sy)+padding]
    if not (0<=box[0]<box[2]<=w and 0<=box[1]<box[3]<=h): raise ValueError("Panel 투영 경계 이탈")
    return box


def _legacy_geometry(report, labels):
    """이전 Run 호환: 기록된 생성 Config로 복원하고 기존 Slot ROI와 교차 검사한다."""
    scene=report["scene_config"]; camera=report["camera"]
    if camera["projection"]!="orthographic": raise ValueError("이전 Run 복원은 정면 직교 카메라만 지원합니다")
    if abs(camera["position"][0]-camera["target"][0])>1e-8 or abs(camera["position"][2]-camera["target"][2])>1e-8:
        raise ValueError("정면 중앙 카메라가 아닙니다")
    ref=scene["camera"]; c=ref["reference"]["position"]
    def normalize(v):
        size=math.sqrt(sum(x*x for x in v))
        return [x/size for x in v]
    f=normalize([t-p for t,p in zip(ref["reference"]["target"],c)])
    right=normalize([f[1],-f[0],0])
    up=[right[1]*f[2]-right[2]*f[1],right[2]*f[0]-right[0]*f[2],right[0]*f[1]-right[1]*f[0]]
    def point(x,y):
        w,h=ref["resolution"]
        ray=[f[i]+right[i]*(x-w/2)/ref["focal_px"]-up[i]*(y-h/2)/ref["focal_px"] for i in range(3)]
        factor=(-.026-c[1])/ray[1]
        return [c[i]+ray[i]*factor for i in range(3)]
    by_slot=defaultdict(list)
    for row in labels: by_slot[row["slot_id"]].append(row)
    result=[]
    for panel in scene["panels"]:
        boxes=[]
        for module in panel["modules"]:
            l,t,r,b=module["bbox"]
            center=point((l+r)/2,(t+b)/2)
            width=point(r,(t+b)/2)[0]-point(l,(t+b)/2)[0]
            height=point((l+r)/2,t)[2]-point((l+r)/2,b)[2]
            boxes.append(_project_box([center[0]-width/2,center[2]-height/2,center[0]+width/2,center[2]+height/2],camera))
            d=scene["display"]; vacuum=module["id"]=="vacuum"
            sw=width*d["vacuum_main_width" if vacuum else "main_width"]
            dh=height*d["vacuum_digit_height" if vacuum else "digit_height"]
            x=center[0]+(d["vacuum_main_x" if vacuum else "main_x"]-.5)*width
            for n in (1,2):
                z=center[2]+(.5-d["slot_y"][n-1])*height
                predicted=_project_box([x-sw/2,z-dh/2,x+sw/2,z+dh/2],camera,report["config"]["crop"]["padding_px"])
                sid=f"{panel['id']}/{module['id']}/slot_{n}"
                if not by_slot[sid] or any(max(abs(a-b) for a,b in zip(predicted,row["slot_roi"]))>1 for row in by_slot[sid]):
                    raise ValueError(f"기록된 숫자 ROI와 복원 Geometry 불일치: {sid}; 새 생성기로 다시 캡처하세요")
        result.append({"panel_id":panel["id"],"housing_bbox":[min(b[0] for b in boxes),min(b[1] for b in boxes),max(b[2] for b in boxes),max(b[3] for b in boxes)]})
    return result


def panel_regions(report, labels, padding):
    source="recorded_usd_housing_bounds" if "panel_regions" in report else "config_reconstruction_checked_against_slot_rois"
    regions=report.get("panel_regions") or _legacy_geometry(report,labels)
    expected={p["id"] for p in report["scene_config"]["panels"]}
    if len(regions)!=7 or {p["panel_id"] for p in regions}!=expected: raise ValueError("7개 Panel 연결 불일치")
    w,h=report["camera"]["resolution"]
    boxes={}
    for row in regions:
        l,t,r,b=row["housing_bbox"]
        box=[l-padding,t-padding,r+padding,b+padding]
        local_box(box,[0,0,w,h])
        boxes[row["panel_id"]]=box
    return boxes,source


def export_run(run, output=None, config_path=None, class_mode=None):
    from PIL import Image, ImageDraw
    from src.dataset.validate_training_capture import validate as validate_source
    run=Path(run).resolve()
    cfg=read_config(config_path,class_mode)
    report=json.loads((run/"manifest.json").read_text(encoding="utf-8"))
    if report["status"]!="PASS": raise ValueError("PASS인 CP 생성 Run만 변환할 수 있습니다")
    validate_source(run)
    frames=[json.loads(s) for s in (run/"frames.jsonl").read_text(encoding="utf-8").splitlines()]
    labels=[json.loads(s) for s in (run/"labels.jsonl").read_text(encoding="utf-8").splitlines()]
    split=frame_split([f["frame_id"] for f in frames],cfg["split_seed"],cfg["validation_fraction"])
    boxes,geometry_source=panel_regions(report,labels,cfg["panel_padding_px"])
    names=["slot"] if cfg["class_mode"]=="single" else [s.replace("/","_") for s in SLOTS]
    out=Path(output).resolve() if output else run/"yolo_panels"
    if out.exists(): raise FileExistsError(f"출력 폴더가 이미 있습니다. --output으로 새 경로를 지정하세요: {out}")
    out.mkdir(parents=True)
    git=lambda *a:subprocess.run(["git",*a],cwd=ROOT,capture_output=True,text=True,check=True).stdout.strip()
    manifest={"schema_version":1,"status":"RUNNING","source_run":str(run),"source_run_id":report["run_id"],
              "created_utc":datetime.now(timezone.utc).isoformat(),"source_seed":report["seed"],"config":cfg,"names":names,
              "source_manifest_sha256":digest(run/"manifest.json"),"source_labels_sha256":digest(run/"labels.jsonl"),
              "source_frames_sha256":digest(run/"frames.jsonl"),"exporter_sha256":digest(__file__),
              "git_base_commit":git("rev-parse","HEAD"),"git_dirty":bool(git("status","--porcelain")),
              "panel_geometry_source":geometry_source,"panel_boxes":boxes,"frame_split":split,
              "panel_count":0,"box_count":0,"limitations":["Synthetic 내부 Train/Val 분할이며 실제 영상 성능 평가 아님","보조 숫자와 버튼 표기는 검출 대상에서 제외","클래스는 숫자 값이 아니라 Slot 영역"]}
    def save(): (out/"manifest.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding="utf-8")
    save()
    try:
        for part in ("train","val"):
            (out/"images"/part).mkdir(parents=True)
            (out/"labels"/part).mkdir(parents=True)
        (out/"previews").mkdir()
        by_frame=defaultdict(list)
        for row in labels: by_frame[row["frame_id"]].append(row)
        previews=[]
        with (out/"annotations.jsonl").open("w",encoding="utf-8") as annotations:
            for frame in frames:
                fid=frame["frame_id"]; part=split[fid]
                with Image.open(run/frame["image"]) as image:
                    image=image.convert("RGB")
                    for panel_id,box in boxes.items():
                        crop=image.crop(box)
                        base=f"{report['run_id']}_{fid}_{panel_id}"
                        image_path=f"images/{part}/{base}.png"
                        label_path=f"labels/{part}/{base}.txt"
                        rows=[r for r in by_frame[fid] if r["slot_id"].split('/')[0]==panel_id]
                        rows.sort(key=lambda r:SLOTS.index(r["slot_id"].split('/',1)[1]))
                        if len(rows)!=6 or {r["slot_id"].split('/',1)[1] for r in rows}!=set(SLOTS): raise ValueError("Panel의 6개 Slot 연결 오류")
                        objects=[]; lines=[]
                        for row in rows:
                            relative=local_box(row[cfg["bbox_source"]],box)
                            xywh=normalized_box(relative,*crop.size)
                            cls=0 if cfg["class_mode"]=="single" else SLOTS.index(row["slot_id"].split('/',1)[1])
                            lines.append(f"{cls} "+" ".join(f"{v:.8f}" for v in xywh))
                            objects.append({"class_id":cls,"slot_id":row["slot_id"],"text":row["text"],
                                            "source_bbox":row[cfg["bbox_source"]],"bbox":relative,"xywhn":xywh})
                        crop.save(out/image_path)
                        (out/label_path).write_text("\n".join(lines)+"\n",encoding="utf-8")
                        record={"image":image_path,"label":label_path,"image_sha256":digest(out/image_path),"label_sha256":digest(out/label_path),
                                "size":list(crop.size),"panel_id":panel_id,"frame_id":fid,"frame_index":frame["frame_index"],
                                "split":part,"source_image":frame["image"],"source_image_sha256":frame["sha256"],"panel_bbox":box,"objects":objects}
                        annotations.write(json.dumps(record,ensure_ascii=False)+"\n")
                        manifest["panel_count"]+=1;manifest["box_count"]+=6
                        if frame is frames[0]:
                            preview=crop.copy();draw=ImageDraw.Draw(preview)
                            for obj in objects:
                                draw.rectangle(obj["bbox"],outline="red",width=2)
                                l,t,_,_=obj["bbox"]
                                draw.text((l,max(0,t-12)),str(obj["class_id"]),fill="white",stroke_width=1,stroke_fill="black")
                            preview.save(out/"previews"/f"{panel_id}.png")
                            previews.append((panel_id,preview))
        # JSON은 YAML의 하위 집합이며 Ultralytics의 YAML loader로 읽을 수 있다.
        dataset={"path":out.as_posix(),"train":"images/train","val":"images/val","names":{str(i):n for i,n in enumerate(names)}}
        (out/"dataset.yaml").write_text(json.dumps(dataset,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
        sheet=Image.new("RGB",(max(im.width for _,im in previews),sum(im.height+24 for _,im in previews)),"#242424")
        draw=ImageDraw.Draw(sheet); y=0
        for pid,im in previews:
            draw.text((5,y+5),pid,fill="white");sheet.paste(im,(0,y+24));y+=im.height+24
        sheet.save(out/"previews/contact_sheet.png")
        manifest["annotations_sha256"]=digest(out/"annotations.jsonl")
        manifest["dataset_yaml_sha256"]=digest(out/"dataset.yaml")
        manifest["status"]="GENERATED";save()
        result=validate_export(out)
        manifest["status"]="PASS";save()
        print(f"PANEL_YOLO_OK: {out} ({result['images']} images, {result['boxes']} boxes)",flush=True)
        return out
    except BaseException as exc:
        manifest["status"]="FAILED";manifest["error"]=str(exc);save()
        raise


def validate_export(out):
    from PIL import Image
    import numpy as np
    out=Path(out).resolve()
    manifest=json.loads((out/"manifest.json").read_text(encoding="utf-8"))
    if manifest["status"] not in ("GENERATED","PASS"): raise ValueError("미완료 YOLO Run")
    run=Path(manifest["source_run"])
    for filename,key in [("manifest.json","source_manifest_sha256"),("labels.jsonl","source_labels_sha256"),("frames.jsonl","source_frames_sha256")]:
        if digest(run/filename)!=manifest[key]: raise ValueError("원본 Run 변경")
    if digest(out/"annotations.jsonl")!=manifest["annotations_sha256"] or digest(out/"dataset.yaml")!=manifest["dataset_yaml_sha256"]:
        raise ValueError("변환 메타데이터 Hash 불일치")
    dataset=json.loads((out/"dataset.yaml").read_text(encoding="utf-8"))
    if dataset!={"path":out.as_posix(),"train":"images/train","val":"images/val","names":{str(i):n for i,n in enumerate(manifest["names"])}}:
        raise ValueError("YOLO dataset.yaml 연결 오류")
    source={(r["frame_id"],r["slot_id"]):r for r in map(json.loads,(run/"labels.jsonl").read_text(encoding="utf-8").splitlines())}
    records=list(map(json.loads,(out/"annotations.jsonl").read_text(encoding="utf-8").splitlines()))
    if len(records)!=manifest["panel_count"] or len(records)*6!=manifest["box_count"]: raise ValueError("출력 개수 오류")
    seen=set(); group_splits=defaultdict(set); counts=defaultdict(int); source_pixels={}
    for row in records:
        key=(row["frame_id"],row["panel_id"])
        if key in seen: raise ValueError("Panel 중복")
        seen.add(key);group_splits[row["frame_id"]].add(row["split"]);counts[row["split"]]+=1
        if row["split"]!=manifest["frame_split"][row["frame_id"]]: raise ValueError("Split 연결 오류")
        if row["panel_bbox"]!=manifest["panel_boxes"][row["panel_id"]]: raise ValueError("Panel 경계 연결 오류")
        if Path(row["image"]).parent.as_posix()!=f"images/{row['split']}" or Path(row["label"]).parent.as_posix()!=f"labels/{row['split']}" or Path(row["image"]).stem!=Path(row["label"]).stem:
            raise ValueError("YOLO 폴더/파일 이름 연결 오류")
        for name,hash_key in (("image","image_sha256"),("label","label_sha256")):
            path=(out/row[name]).resolve()
            if not path.is_relative_to(out) or digest(path)!=row[hash_key]: raise ValueError("파일 경로/Hash 오류")
        if row["frame_id"] not in source_pixels:
            path=(run/row["source_image"]).resolve()
            if not path.is_relative_to(run) or digest(path)!=row["source_image_sha256"]: raise ValueError("원본 이미지 연결 오류")
            with Image.open(path) as im: pixels=np.array(im.convert("RGB"))
            source_pixels={row["frame_id"]:pixels}  # 프레임 하나만 캐시
        pixels=source_pixels[row["frame_id"]]
        l,t,r,b=row["panel_bbox"]
        local_box([l,t,r,b],[0,0,pixels.shape[1],pixels.shape[0]])
        with Image.open(out/row["image"]) as im:
            if list(im.size)!=row["size"] or not np.array_equal(np.array(im.convert("RGB")),pixels[t:b,l:r]): raise ValueError("Panel Crop 픽셀 불일치")
        lines=(out/row["label"]).read_text(encoding="utf-8").splitlines()
        if len(lines)!=6 or len(row["objects"])!=6: raise ValueError("YOLO 라벨은 Panel마다 6개여야 합니다")
        if {o["slot_id"].split('/',1)[1] for o in row["objects"]}!=set(SLOTS): raise ValueError("6개 Slot 누락")
        for line,obj in zip(lines,row["objects"]):
            if obj["slot_id"].split('/')[0]!=row["panel_id"]: raise ValueError("Slot의 Panel 연결 오류")
            parts=line.split()
            if len(parts)!=5: raise ValueError("YOLO 열 수 오류")
            cls=int(parts[0]); values=[float(v) for v in parts[1:]]
            expected_class=0 if manifest["config"]["class_mode"]=="single" else SLOTS.index(obj["slot_id"].split('/',1)[1])
            if cls!=expected_class: raise ValueError("Slot 클래스 배정 오류")
            if cls!=obj["class_id"] or not 0<=cls<len(manifest["names"]) or not all(math.isfinite(v) and 0<=v<=1 for v in values): raise ValueError("YOLO 클래스/좌표 오류")
            source_row=source[(row["frame_id"],obj["slot_id"])]
            expected=source_row[manifest["config"]["bbox_source"]]
            if obj["text"]!=source_row["text"] or obj["source_bbox"]!=expected or obj["bbox"]!=local_box(expected,row["panel_bbox"]): raise ValueError("원본 Slot/정답 연결 오류")
            x,y,w,h=values; iw,ih=row["size"]
            decoded=[(x-w/2)*iw,(y-h/2)*ih,(x+w/2)*iw,(y+h/2)*ih]
            if w<=0 or h<=0 or max(abs(a-b) for a,b in zip(decoded,obj["bbox"]))>.001: raise ValueError("정규화 역변환 불일치")
    if any(len(v)!=1 for v in group_splits.values()) or not counts["train"] or not counts["val"]: raise ValueError("프레임 Split 누수/빈 분할")
    if seen!={(fid,pid) for fid in manifest["frame_split"] for pid in manifest["panel_boxes"]}: raise ValueError("Frame/Panel 조합 누락")
    expected_images={row["image"] for row in records}; expected_labels={row["label"] for row in records}
    if {p.relative_to(out).as_posix() for p in (out/"images").rglob("*.png")}!=expected_images or {p.relative_to(out).as_posix() for p in (out/"labels").rglob("*.txt")}!=expected_labels: raise ValueError("라벨/이미지 쌍 오류")
    result={"status":"PASS","images":len(records),"boxes":len(records)*6,"split_images":dict(counts),"original_frames":len(group_splits),"frame_split_leakage":False,"validator_sha256":digest(__file__)}
    (out/"validation.json").write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
    return result


if __name__=="__main__":
    parser=argparse.ArgumentParser(description="CP Run → 7개 Panel/프레임과 YOLO Slot 라벨")
    parser.add_argument("run",type=Path)
    parser.add_argument("--output",type=Path)
    parser.add_argument("--config",type=Path)
    parser.add_argument("--class-mode",choices=("single","six_slots"))
    parser.add_argument("--validate-only",action="store_true",help="run 위치의 YOLO 출력만 재검증")
    args=parser.parse_args()
    if args.validate_only: print(json.dumps(validate_export(args.run),ensure_ascii=False))
    else: export_run(args.run,args.output,args.config,args.class_mode)
