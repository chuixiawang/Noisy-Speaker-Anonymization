import unittest

from casr.metrics import (
    character_error_counts,
    eer_percent,
    error_rate_percent,
    normalize_transcript,
    word_error_counts,
)


class MetricTests(unittest.TestCase):
    def test_normalization(self):
        self.assertEqual(normalize_transcript("Hello,  WORLD!"), "hello world")

    def test_word_error_rate(self):
        counts = word_error_counts("a b c", "a x c")
        self.assertEqual(counts["S"], 1)
        self.assertAlmostEqual(error_rate_percent(counts), 100.0 / 3.0)

    def test_character_error_rate(self):
        counts = character_error_counts("abc", "adc")
        self.assertEqual(counts["S"], 1)

    def test_eer(self):
        value = eer_percent([0.9, 0.8, 0.2, 0.1], [1, 1, 0, 0])
        self.assertEqual(value, 0.0)


if __name__ == "__main__":
    unittest.main()
