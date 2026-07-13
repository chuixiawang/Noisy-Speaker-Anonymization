import unittest

import numpy as np

from casr.noise import add_white_noise, mix_at_snr, rms


class NoiseTests(unittest.TestCase):
    def test_white_noise_is_deterministic(self):
        clean = np.ones(1600, dtype=np.float32) * 0.1
        first = add_white_noise(clean, 10, seed=2026)
        second = add_white_noise(clean, 10, seed=2026)
        np.testing.assert_allclose(first, second)

    def test_mix_reaches_target_snr_without_peak_normalization(self):
        clean = np.ones(1600, dtype=np.float32) * 0.01
        noise = np.tile(np.array([-1.0, 1.0], dtype=np.float32), 800)
        mixed = mix_at_snr(clean, noise, 10)
        measured = 20.0 * np.log10(rms(clean) / rms(mixed - clean))
        self.assertAlmostEqual(measured, 10.0, places=4)


if __name__ == "__main__":
    unittest.main()
