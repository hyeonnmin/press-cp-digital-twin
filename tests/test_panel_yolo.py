import unittest
from src.dataset.panel_yolo import frame_split,local_box,normalized_box,read_config


class PanelYoloTests(unittest.TestCase):
    def test_known_crop_and_yolo_coordinates(self):
        # 원본 [110, 70, 150, 90] → Panel 원점 [100, 50], 크기 200×100.
        box=local_box([110,70,150,90],[100,50,300,150])
        self.assertEqual(box,[10,20,50,40])
        self.assertEqual(normalized_box(box,200,100),[.15,.3,.2,.2])

    def test_reject_truncation_and_invalid_boxes(self):
        for box in ([99,60,120,80],[110,40,120,80],[120,80,110,90],[100,50,301,150],[float('nan'),60,120,80]):
            with self.assertRaises(ValueError): local_box(box,[100,50,300,150])
        with self.assertRaises(ValueError): normalized_box([0,0,0,1],10,10)

    def test_split_whole_frames_reproducibly(self):
        ids=[f"frame_{i}" for i in range(10)]
        split=frame_split(ids,42,.2)
        self.assertEqual(split,frame_split(ids[::-1],42,.2))
        self.assertEqual(list(split.values()).count('val'),2)
        self.assertEqual(set(split),set(ids))
        with self.assertRaises(ValueError): frame_split(['only_one'],42,.2)

    def test_single_slot_is_default(self):
        self.assertEqual(read_config()['class_mode'],'single')
