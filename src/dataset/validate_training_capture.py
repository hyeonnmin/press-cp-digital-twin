"""Isaac Sim 외부에서 저장 이미지·정답·Seed·Crop·안정화 기록을 재검증한다."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

import numpy as np
from PIL import Image

ROOT=Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from src.generation.random_values import RandomValues,slot_ids


def digest(path): return hashlib.sha256(path.read_bytes()).hexdigest()


def validate(run):
    run=Path(run)
    report=json.loads((run/"manifest.json").read_text(encoding="utf-8"))
    if report["status"] not in ("GENERATED","PASS"): raise ValueError("미완료/실패 Run은 학습에 사용할 수 없습니다")
    config=report["config"]
    frames=[json.loads(s) for s in (run/"frames.jsonl").read_text(encoding="utf-8").splitlines()]
    labels=[json.loads(s) for s in (run/"labels.jsonl").read_text(encoding="utf-8").splitlines()]
    assert digest(run/"frames.jsonl")==report["frames_sha256"]
    assert digest(run/"labels.jsonl")==report["labels_sha256"]
    assert len(frames)==report["frame_count"]==config["frame_count"]
    assert len(labels)==report["crop_count"]==len(frames)*42
    assert len({r["image"] for r in labels})==len(labels)
    assert len({r["image"] for r in frames})==len(frames)
    generator=RandomValues(report["seed"],config["sampling"])
    expected_ids=set(slot_ids(report["scene_config"]))
    def image(path,sha=None):
        path=run/path
        assert path.resolve().is_relative_to(run.resolve()),"Run 외부 파일 참조"
        if sha: assert digest(path)==sha
        with Image.open(path) as im:
            im.load()
            return np.array(im.convert("RGB"))
    def settle_check(record):
        checks=record["checks"]
        n=config["render"]["stable_checks"]
        assert record["consecutive_passes"]>=n and len(checks)>=n
        assert record["subframes"]==checks[-1]["subframes"]<=config["render"]["max_subframes"]
        assert all(c["maximum_slot_mean_difference"]<=config["render"]["max_roi_mean_difference"] for c in checks[-n:])
    heights=[]
    for index,frame in enumerate(frames):
        expected=generator.frame(index,report["scene_config"])
        assert frame["slots"]==expected["slots"] and frame["frame_index"]==index,"Seed 기반 정답 재현 불일치"
        pixels=image(frame["image"],frame["sha256"])
        assert list(pixels.shape[:2][::-1])==config["camera"]["resolution"]
        settle_check(frame["settle"])
        rows=[r for r in labels if r["frame_id"]==frame["frame_id"]]
        assert len(rows)==42 and {r["slot_id"] for r in rows}==expected_ids
        expected_text={r["slot_id"]:r["text"] for r in expected["slots"]}
        for row in rows:
            assert row["text"]==expected_text[row["slot_id"]]
            assert row["run_id"]==report["run_id"] and row["frame_index"]==index
            assert row["frame_image"]==frame["image"] and row["split"]==report["split"]
            l,t,r,b=row["bbox"]
            assert 0<=l<r<=pixels.shape[1] and 0<=t<b<=pixels.shape[0]
            assert np.array_equal(image(row["image"],row["sha256"]),pixels[t:b,l:r]),"Crop 픽셀 불일치"
            dl,dt,dr,db=row["digit_bbox"]
            assert l<=dl<dr<=r and t<=dt<db<=b
            assert db-dt==row["digit_height_px"]>=config["crop"]["minimum_digit_height_px"]
            heights.append(row["digit_height_px"])
            for other in rows:
                if other is row: continue
                ol,ot,orr,ob=other["digit_bbox"]
                assert min(r,orr)<=max(l,ol) or min(b,ob)<=max(t,ot),"다른 Slot 숫자가 Crop에 포함됨"
    probes=report["verification"]["probes"]
    assert [p["text"] for p in probes]==["0.0","999.0","0.0"]
    probe_pixels=[image(p["image"],p["sha256"]) for p in probes]
    for p in probes: settle_check(p["settle"])
    for row in report["verification"]["repeat_checks"]:
        l,t,r,b=row["slot_roi"]
        same=float(np.abs(probe_pixels[2][t:b,l:r].astype(float)-probe_pixels[0][t:b,l:r]).mean())
        wrong=float(np.abs(probe_pixels[2][t:b,l:r].astype(float)-probe_pixels[1][t:b,l:r]).mean())
        assert wrong>.1 and same<wrong*config["verification"]["maximum_repeat_ratio"]
        assert abs(same-row["repeat_difference"])<1e-8
    result={"status":"PASS","frames":len(frames),"crops":len(labels),"minimum_digit_height_px":min(heights),
            "maximum_digit_height_px":max(heights),"validator_sha256":digest(Path(__file__)),
            "scope":"Seed 재현·문자열·파일 Hash·Crop 픽셀·영역 중첩·안정화 기록·동일 값 복귀. 독립 OCR 판독 아님"}
    (run/"validation.json").write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
    return result


if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("run",type=Path)
    args=parser.parse_args()
    print(json.dumps(validate(args.run),ensure_ascii=False))
