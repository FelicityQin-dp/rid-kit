import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from rid.utils.set_config import normalize_std_threshold


class TestSetConfig(unittest.TestCase):
    def test_normalize_std_threshold_scalar(self):
        self.assertEqual(normalize_std_threshold(2.0, 3), [2.0, 2.0, 2.0])

    def test_normalize_std_threshold_single_element_list(self):
        self.assertEqual(normalize_std_threshold([1.5], 2), [1.5, 1.5])

    def test_normalize_std_threshold_per_cv(self):
        self.assertEqual(
            normalize_std_threshold([1.5, 10.0], 2),
            [1.5, 10.0],
        )

    def test_normalize_std_threshold_length_mismatch(self):
        with self.assertRaises(ValueError):
            normalize_std_threshold([1.0, 2.0, 3.0], 2)


if __name__ == "__main__":
    unittest.main()
