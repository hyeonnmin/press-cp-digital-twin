"""Isaac Sim과 독립적인 순차 표시 문자열 생성기."""
import argparse
from decimal import Decimal, InvalidOperation
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


class SequentialValues:
    def __init__(self, config):
        self.config = dict(config)
        places = config["decimal_places"]
        if type(places) is not int or places < 0:
            raise ValueError("decimal_places는 0 이상의 정수여야 합니다")
        self.places = places
        self.scale = 10 ** places
        numbers = []
        for key in ("minimum", "maximum", "start", "step"):
            try:
                value = Decimal(str(config[key]))
            except (InvalidOperation, ValueError) as exc:
                raise ValueError(f"잘못된 숫자: {key}") from exc
            if not value.is_finite() or value * self.scale != (value * self.scale).to_integral_value():
                raise ValueError(f"표시 정밀도에 맞지 않는 값: {key}")
            numbers.append(int(value * self.scale))
        self.minimum, self.maximum, self.start, self.step = numbers
        if self.minimum > self.maximum or not self.minimum <= self.start <= self.maximum or self.step <= 0:
            raise ValueError("범위, 시작값 또는 증가 폭이 잘못되었습니다")
        if (self.maximum - self.minimum) % self.step or (self.start - self.minimum) % self.step:
            raise ValueError("시작값과 최대값은 증가 폭으로 도달할 수 있어야 합니다")
        if type(config["wrap"]) is not bool:
            raise ValueError("wrap은 bool이어야 합니다")
        if config["slot_mode"] != "synchronized":
            raise ValueError("현재 Slot 동기화 방식만 지원합니다")
        self.wrap = config["wrap"]
        self.count = (self.maximum - self.minimum) // self.step + 1

    def text_at(self, frame_index):
        if type(frame_index) is not int or frame_index < 0:
            raise ValueError("프레임 번호는 0 이상의 정수여야 합니다")
        index = (self.start - self.minimum) // self.step + frame_index
        if not self.wrap and index >= self.count:
            raise IndexError("순차 값 범위를 모두 생성했습니다")
        value = self.minimum + (index % self.count) * self.step
        return format(Decimal(value) / self.scale, f".{self.places}f")

    def frame(self, frame_index, scene_config):
        text = self.text_at(frame_index)
        return {
            "frame_index": frame_index,
            "slots": [
                {"slot_id": f"{panel['id']}/{module['id']}/slot_{slot}", "text": text}
                for panel in scene_config["panels"]
                for module in panel["modules"]
                for slot in (1, 2)
            ],
        }


def main():
    parser = argparse.ArgumentParser(description="순차 문자열 확인. 이미지 캡처는 수행하지 않습니다.")
    parser.add_argument("--config", type=Path, default=ROOT / "config/dataset_capture.json")
    parser.add_argument("--frame-index", type=int, default=0)
    args = parser.parse_args()
    config = json.loads(args.config.read_text(encoding="utf-8"))
    scene = json.loads((ROOT / "config/press_cp_scene.json").read_text(encoding="utf-8"))
    print(json.dumps(SequentialValues(config["sequence"]).frame(args.frame_index, scene), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
