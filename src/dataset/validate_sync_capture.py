"""저장 결과를 Isaac Sim 없이 다시 읽어 이미지·문자열·연결을 검사한다."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from src.generation.value_generator import SequentialValues


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate(run):
    report = json.loads((run / "report.json").read_text(encoding="utf-8"))
    labels_path = run / "labels.jsonl"
    if digest(labels_path) != report["labels_sha256"]: raise AssertionError("Label Hash 불일치")
    labels = [json.loads(line) for line in labels_path.read_text(encoding="utf-8").splitlines()]
    values = SequentialValues(report["config"]["sequence"])
    if len(labels) != report["crop_count"] or len(report["frames"]) != report["frame_count"]: raise AssertionError("수량 불일치")
    if len({r["image"] for r in labels}) != len(labels): raise AssertionError("중복 이미지")
    expected_ids = {r["id"] for r in report["roi_config"]["slots"]}
    pictures = []
    for n, frame in enumerate(report["frames"]):
        path = run / frame["image"]
        if digest(path) != frame["sha256"]: raise AssertionError("프레임 Hash 불일치")
        with Image.open(path) as image:
            image.load()
            pixels = np.asarray(image.convert("RGB")).copy()
        if pixels.shape[:2] != tuple(reversed(report["scene_config"]["camera"]["resolution"])): raise AssertionError("해상도 불일치")
        pictures.append(pixels)
        rows = [r for r in labels if r["frame_id"] == f"frame_{n:06d}"]
        if len(rows) != 42 or {r["slot_id"] for r in rows} != expected_ids: raise AssertionError("Slot 연결 불일치")
        slots = {s["slot_id"]: s for s in frame["slots"]}
        for row in rows:
            expected = values.text_at(frame["frame_index"])
            if row["text"] != expected or row["text"] != slots[row["slot_id"]]["text"] or frame["text"] != expected:
                raise AssertionError("정답 문자열 불일치")
            if row["frame_index"] != frame["frame_index"] or row["frame_image"] != frame["image"] or row["run_id"] != report["run_id"]:
                raise AssertionError("프레임 연결 불일치")
            path = run / row["image"]
            if digest(path) != row["image_sha256"]: raise AssertionError("Crop Hash 불일치")
            l,t,r,b = row["bbox"]
            if not (0 <= l < r <= pixels.shape[1] and 0 <= t < b <= pixels.shape[0]): raise AssertionError("ROI 경계 이탈")
            with Image.open(path) as crop:
                if not np.array_equal(np.asarray(crop.convert("RGB")), pixels[t:b,l:r]): raise AssertionError("Crop과 원본 픽셀 불일치")
    repeats = []
    for n in range(1, len(pictures)):
        for earlier in range(n):
            if report["frames"][earlier]["text"] != report["frames"][n]["text"]: continue
            for roi in report["roi_config"]["slots"]:
                l,t,r,b = roi["bbox"]
                same = float(np.abs(pictures[n][t:b,l:r].astype(float)-pictures[earlier][t:b,l:r]).mean())
                wrong = float(np.abs(pictures[n][t:b,l:r].astype(float)-pictures[n-1][t:b,l:r]).mean())
                if report["frames"][n-1]["text"] != report["frames"][n]["text"] and not same < wrong*.25:
                    raise AssertionError(f"반복값 영상이 이전 다른 값에 가까움: {roi['id']}")
                repeats.append({"slot_id":roi["id"],"same_text_mean_difference":same,"previous_text_mean_difference":wrong})
    # 원본 Crop은 그대로 두고 검토용 표만 최근접 확대한다.
    sheet = Image.new("RGB", (240*len(pictures), 32+60*42), "#242424")
    draw = ImageDraw.Draw(sheet)
    for n, frame in enumerate(report["frames"]):
        draw.text((n*240+8,8), f"index {frame['frame_index']} / {frame['text']}", fill="white")
        rows = [r for r in labels if r["frame_id"] == f"frame_{n:06d}"]
        for i,row in enumerate(rows):
            with Image.open(run / row["image"]) as crop:
                preview = crop.convert("RGB")
                preview.thumbnail((220,38), Image.Resampling.NEAREST)
                # 작은 원본도 최대 2배까지 확대
                scale = min(2,220/preview.width,38/preview.height)
                preview = preview.resize((int(preview.width*scale),int(preview.height*scale)),Image.Resampling.NEAREST)
                sheet.paste(preview,(n*240+8,32+i*60+18))
            draw.text((n*240+8,32+i*60),row["slot_id"],fill="white")
    sheet.save(run / "contact_sheet.png")
    result = {"status":"PASS","frame_count":len(pictures),"crop_count":len(labels),"repeat_checks":repeats,
              "contact_sheet":"contact_sheet.png", "validator_sha256":digest(Path(__file__)),
              "scope":"파일·문자열·Crop 픽셀 연결과 동일 값 복귀 검사. OCR 독립 판독 아님"}
    (run / "validation.json").write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps({"status":"PASS","frames":len(pictures),"crops":len(labels),"repeat_slots":len(repeats)},ensure_ascii=False))
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("run", type=Path)
    validate(parser.parse_args().run)
