"""전 범위의 숫자 선택·자릿수·크기·정렬 검사."""
import unittest
from src.generation.glyph_layout import glyph_layout


class GlyphLayoutTests(unittest.TestCase):
    def test_digit_selection(self):
        self.assertEqual([r[0] for r in glyph_layout("0.0",.04,.01)], ["digit_2_0","decimal","digit_3_0"])
        self.assertEqual([r[0] for r in glyph_layout("999.0",.04,.01)], ["digit_0_9","digit_1_9","digit_2_9","decimal","digit_3_0"])

    def test_complete_range(self):
        for value in range(9991):
            text=f"{value//10}.{value%10}"
            layout=glyph_layout(text,.04,.01)
            self.assertEqual(len(layout),len(text))
            self.assertEqual(len({r[0] for r in layout}),len(text))
            self.assertTrue(all(0 < r[2] <= .01 for r in layout))
            self.assertTrue(all(a[1]<b[1] for a,b in zip(layout,layout[1:])))
            self.assertAlmostEqual(layout[-1][1]+.34*layout[-1][2],.02)

    def test_invalid_text(self):
        for text in ("", "1", "1000.0", "0.01", "1..0", "-1.0", "x.0"):
            with self.subTest(text=text),self.assertRaises(ValueError): glyph_layout(text,.04,.01)


if __name__ == "__main__": unittest.main()
