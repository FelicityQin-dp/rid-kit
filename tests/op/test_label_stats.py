import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from dflow.python import OPIO

from rid.op.label_stats import LabelStats
from rid.constants import cv_force_out, mf_std_fig


class TestLabelStats(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.task_paths = []
        self.mf_info_paths = []
        self.cv_forces_paths = []

        std_rows = [
            [1.0, 2.0],
            [3.0, 1.0],
            [1.0, 8.0],
        ]
        for idx, std_row in enumerate(std_rows):
            task_path = Path(self.tmpdir) / f"task_{idx}"
            task_path.mkdir()
            cv_force_path = task_path / cv_force_out
            with open(cv_force_path, "w") as handle:
                handle.write("1.0 2.0 0.1 0.2\n")
            mf_info_path = task_path / "mf_info.out"
            with open(mf_info_path, "w") as handle:
                handle.write("cv list value      1.0 2.0\n")
                handle.write("mean force value   0.1 0.2\n")
                handle.write(
                    "mean force std     "
                    + " ".join(f"{value:.4f}" for value in std_row)
                    + "\n"
                )
            self.cv_forces_paths.append(cv_force_path)
            self.mf_info_paths.append(mf_info_path)

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def _execute(self, std_threshold):
        op = LabelStats()
        return op.execute(
            OPIO(
                {
                    "cv_forces": self.cv_forces_paths,
                    "mf_info": self.mf_info_paths,
                    "std_threshold": std_threshold,
                }
            )
        )

    def test_scalar_broadcast_threshold(self):
        op_out = self._execute([5.0, 5.0])
        self.assertEqual(len(op_out["cv_forces"]), 2)
        self.assertTrue(op_out["mf_std_fig"].exists())

    def test_per_cv_threshold(self):
        op_out = self._execute([2.0, 5.0])
        self.assertEqual(len(op_out["cv_forces"]), 1)

    def test_per_cv_threshold_filters_sample(self):
        op_out = self._execute([2.0, 7.0])
        self.assertEqual(len(op_out["cv_forces"]), 1)

    def test_all_samples_filtered(self):
        op_out = self._execute([0.5, 0.5])
        self.assertEqual(len(op_out["cv_forces"]), 0)

    def test_threshold_length_mismatch(self):
        with self.assertRaises(ValueError):
            self._execute([1.0, 2.0, 3.0])


if __name__ == "__main__":
    unittest.main()
