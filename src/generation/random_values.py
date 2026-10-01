"""Seed로 재현되는 자릿수 균형 숫자 선택. 문자열 정밀도를 보존한다."""
import random


def slot_ids(scene):
    return [f"{p['id']}/{m['id']}/slot_{n}" for p in scene["panels"] for m in p["modules"] for n in (1, 2)]


class RandomValues:
    def __init__(self, seed, config):
        if type(seed) is not int or seed < 0:
            raise ValueError("seed는 0 이상의 정수여야 합니다")
        if (config["mode"], config["minimum"], config["maximum"], config["decimal_places"]) != (
            "balanced_digit_length", "0.0", "999.0", 1
        ):
            raise ValueError("현재 학습 범위는 0.0~999.0, 소수점 한 자리입니다")
        self.seed = seed

    def frame(self, index, scene):
        if type(index) is not int or index < 0:
            raise ValueError("frame_index는 0 이상의 정수여야 합니다")
        ids = slot_ids(scene)
        if len(ids) != 42 or len(set(ids)) != 42:
            raise ValueError("42개 고유 Slot이 필요합니다")
        rng = random.Random(f"press-cp:{self.seed}:{index}")
        groups = [n % 3 for n in range(len(ids))]
        rng.shuffle(groups)
        ranges = [(0, 99), (100, 999), (1000, 9990)]
        rows = []
        for sid, group in zip(ids, groups):
            value = rng.randint(*ranges[group])
            rows.append({"slot_id": sid, "text": f"{value // 10}.{value % 10}"})
        return {"frame_index": index, "slots": rows}
