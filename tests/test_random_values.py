import json
from pathlib import Path
import unittest
from src.generation.random_values import RandomValues

ROOT=Path(__file__).resolve().parents[1]


class RandomValueTests(unittest.TestCase):
    def test_reproducible_balanced_frames(self):
        config=json.loads((ROOT/"config/training_capture.json").read_text(encoding="utf-8"))
        scene=json.loads((ROOT/"config/press_cp_scene.json").read_text(encoding="utf-8"))
        a=RandomValues(42,config["sampling"])
        b=RandomValues(43,config["sampling"])
        for i in range(100):
            frame=a.frame(i,scene)
            self.assertEqual(frame,RandomValues(42,config["sampling"]).frame(i,scene))
            self.assertNotEqual(frame,b.frame(i,scene))
            texts=[r["text"] for r in frame["slots"]]
            self.assertEqual([sum(len(t.split('.')[0])==n for t in texts) for n in (1,2,3)],[14,14,14])
            self.assertTrue(all(0<=float(t)<=999 and len(t.split('.')[1])==1 for t in texts))
            self.assertGreater(len(set(texts)),30)
