"""전체 순회, 소수점 보존 및 42개 Slot 연결 검증."""
import json
import unittest

from src.generation.value_generator import ROOT, SequentialValues


class SequentialValuesTests(unittest.TestCase):
    def setUp(self):
        self.config = json.loads((ROOT / "config/dataset_capture.json").read_text(encoding="utf-8"))["sequence"]
        self.values = SequentialValues(self.config)

    def test_complete_cycle(self):
        expected = [f"{n // 10}.{n % 10}" for n in range(9991)]
        self.assertEqual([self.values.text_at(n) for n in range(9991)], expected)
        self.assertEqual(self.values.text_at(9991), "0.0")
        self.assertEqual(self.values.text_at(9992), "0.1")

    def test_slots(self):
        scene = json.loads((ROOT / "config/press_cp_scene.json").read_text(encoding="utf-8"))
        slots = self.values.frame(9990, scene)["slots"]
        self.assertEqual(len(slots), 42)
        self.assertEqual(len({slot["slot_id"] for slot in slots}), 42)
        self.assertEqual({slot["text"] for slot in slots}, {"999.0"})

    def test_start_and_stop(self):
        values = SequentialValues(dict(self.config, start="998.9", wrap=False))
        self.assertEqual(values.text_at(0), "998.9")
        self.assertEqual(values.text_at(1), "999.0")
        with self.assertRaises(IndexError):
            values.text_at(2)

    def test_invalid_parameters(self):
        for change in ({"step": "0"}, {"step": "0.01"}, {"maximum": "NaN"}, {"start": "1000.0"}, {"step": "0.4"}):
            with self.subTest(change=change), self.assertRaises(ValueError):
                SequentialValues(dict(self.config, **change))
        for index in (-1, 1.5, True):
            with self.assertRaises(ValueError):
                self.values.text_at(index)


if __name__ == "__main__":
    unittest.main()
