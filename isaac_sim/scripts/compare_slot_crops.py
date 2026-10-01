"""고정 영상 좌표로 실영상/변경 전/후 렌더 42 Slot을 예비 비교한다.

Isaac 앱 없이 C:/isaacsim/python.bat로 실행한다. Pillow와 NumPy만 사용한다.
색 마스크 지표는 관찰 보조치이며 OCR 정답이나 영상 유사성 합격 점수가 아니다.
"""
import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[2]


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def measure(crop, bbox, slot_id):
    rgb = np.asarray(crop, dtype=float)
    red, green, blue = rgb.transpose(2, 0, 1)
    # 두 LED 색에 공통 적용. 어두운 화면과 무채색 반사를 배제한다.
    mask = (red > 75) & (green > 65) & (np.maximum(red, green) - blue > 45)
    # 검색창 가장자리로 들어오는 다른 색 표시줄을 제외한다.
    mask &= green >= red * 0.98 if slot_id.endswith("slot_1") else red >= green * 1.08
    if mask.sum() < 4:
        return {"status": "insufficient_colored_pixels", "pixel_count": int(mask.sum())}
    brightness = np.maximum(red, green)
    core = mask & (brightness >= np.percentile(brightness[mask], 60))
    ys, xs = np.where(core)
    return {
        "status": "measured",
        "pixel_count": int(mask.sum()),
        "core_pixel_count": int(core.sum()),
        "core_rgb_median": np.median(rgb[core], axis=0).round(2).tolist(),
        "core_center_px": [round(float(xs.mean() + bbox[0]), 2), round(float(ys.mean() + bbox[1]), 2)],
        "core_extent_px": [int(xs.max() - xs.min() + 1), int(ys.max() - ys.min() + 1)],
        "background_rgb_median": np.median(rgb[~mask], axis=0).round(2).tolist() if (~mask).any() else None,
        "touches_roi_edge": bool(np.any(core[0]) or np.any(core[-1]) or np.any(core[:, 0]) or np.any(core[:, -1])),
    }


def compare(config_path, before, after, output, render_reports=None):
    cfg = json.loads(config_path.read_text(encoding="utf-8"))
    inputs = {"real": ROOT / cfg["reference_image"], "before": before}
    if after:
        inputs["after"] = after
    assert sha256(inputs["real"]) == cfg["reference_sha256"], "실영상 프레임 Hash 불일치"
    images = {name: Image.open(path).convert("RGB") for name, path in inputs.items()}
    provenance = {}
    for name,path in (render_reports or {}).items():
        if path is None:
            continue
        report = json.loads(path.read_text(encoding="utf-8"))
        assert sha256(inputs[name]) in report["artifact_sha256"].values(), f"{name} 렌더와 보고서 Hash 불일치"
        provenance[name] = {"path": str(path), "sha256": sha256(path), "snapshot": report}
    assert all(im.size == tuple(cfg["resolution"]) for im in images.values()), "해상도 불일치"
    ids = [slot["id"] for slot in cfg["slots"]]
    assert len(ids) == len(set(ids)) == 42, "Slot 42개/고유 ID 오류"
    output.mkdir(parents=True, exist_ok=True)
    crops_dir = output / "crops"
    crops_dir.mkdir(exist_ok=True)
    title_font = ImageFont.truetype("C:/Windows/Fonts/malgun.ttf", 20)
    label_font = ImageFont.truetype("C:/Windows/Fonts/malgun.ttf", 15)
    names = {"real": "실영상 4초", "before": "변경 전 DT", "after": "LED 수정 후 DT"}
    rows = []
    sheets = []
    for panel in range(1, 8):
        panel_slots = [s for s in cfg["slots"] if s["id"].startswith(f"panel_{panel}/")]
        sheet = Image.new("RGB", (1430, 6 * 140 + 85), "#20252c")
        draw = ImageDraw.Draw(sheet)
        draw.text((20, 10), f"Panel {panel} — 같은 영상 좌표 Crop / 4배 최근접 확대", font=title_font, fill="white")
        for column, name in enumerate(images):
            draw.text((270 + column * 380, 48), names[name], font=label_font, fill="#a5d6f2")
        for i, slot in enumerate(panel_slots):
            box = slot["bbox"]
            assert 0 <= box[0] < box[2] <= cfg["resolution"][0]
            assert 0 <= box[1] < box[3] <= cfg["resolution"][1]
            row = {"slot_id": slot["id"], "roi_px": box, "measurements": {}, "crops": {}}
            draw.text((20, 95 + i * 140), slot["id"].split("/", 1)[1], font=label_font, fill="white")
            for column, (name, im) in enumerate(images.items()):
                crop = im.crop(box)
                path = crops_dir / (slot["id"].replace("/", "_") + f"_{name}.png")
                crop.save(path)
                row["crops"][name] = {"path": str(path.relative_to(output)), "sha256": sha256(path)}
                row["measurements"][name] = measure(crop, box, slot["id"])
                enlarged = crop.resize((crop.width * 4, crop.height * 4), Image.Resampling.NEAREST)
                sheet.paste(enlarged, (270 + column * 380, 82 + i * 140))
            rows.append(row)
        path = output / f"panel_{panel}.png"
        sheet.save(path)
        sheets.append(str(path.relative_to(output)))
    summary = {}
    for slot_number in (1, 2):
        summary[f"slot_{slot_number}"] = {}
        group = [r for r in rows if r["slot_id"].endswith(f"slot_{slot_number}")]
        for name in images:
            valid = [r["measurements"][name] for r in group if r["measurements"][name]["status"] == "measured"]
            summary[f"slot_{slot_number}"][name] = {
                "measured": len(valid),
                "median_core_rgb": np.median([m["core_rgb_median"] for m in valid], axis=0).round(2).tolist() if valid else None,
            }
        for name in list(images)[1:]:
            valid = [r for r in group if all(r["measurements"][n]["status"] == "measured" for n in ("real", name))]
            summary[f"slot_{slot_number}"][name]["median_center_offset_px"] = round(float(np.median([
                np.linalg.norm(np.array(r["measurements"][name]["core_center_px"]) - r["measurements"]["real"]["core_center_px"]) for r in valid
            ])), 2) if valid else None
    report = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(), "status": "PRELIMINARY_COMPARISON",
        "scope": "단일 4초 프레임의 예비 외형 비교; Train/Test 미정(2026-10-01 사용자 확인); OCR/Real Test 평가 아님",
        "config": cfg, "config_sha256": sha256(config_path), "script_sha256": sha256(Path(__file__)),
        "inputs": {k: {"path": str(p), "sha256": sha256(p)} for k, p in inputs.items()},
        "render_reports": provenance,
        "metric_note": "고정 ROI 내 녹색/주황색 마스크의 상위 40% 밝기 픽셀. 색/중심 보조 지표이며 문자열 전사·가림·유사도 합격을 검증하지 않음. 두 마스크는 measure()에 고정되어 세 이미지에 동일 적용.",
        "summary": summary, "slots": rows, "sheets": sheets,
    }
    (output / "comparison.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False))
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=ROOT / "config/slot_crop_comparison.json")
    parser.add_argument("--before", type=Path, default=ROOT / "outputs/led_comparison/before_reference.png")
    parser.add_argument("--after", type=Path)
    parser.add_argument("--before-report", type=Path)
    parser.add_argument("--after-report", type=Path)
    parser.add_argument("--output", type=Path, default=ROOT / "outputs/led_comparison/comparison")
    args = parser.parse_args()
    compare(args.config, args.before, args.after, args.output, {"before": args.before_report, "after": args.after_report})
