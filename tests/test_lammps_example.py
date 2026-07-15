import json
import os
import sys
import unittest
from pathlib import Path

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from rid.common.sampler.command import get_mdrun_cmd
from rid.task.builder import build_lmp_dict
from rid.constants import lmp_conf_name


EXAMPLE_ROOT = Path(__file__).resolve().parents[1] / "examples"
LMP_INPUT_DIR = EXAMPLE_ROOT / "lj4_lmp_input"
RID_CONFIG = EXAMPLE_ROOT / "rid_json_files" / "rid_lj4_lmp.json"
MACHINE_CONFIG = EXAMPLE_ROOT / "machine_bohrium_lmp_k8s.json"


class TestLammpsExample(unittest.TestCase):
    def test_example_files_exist(self):
        required_files = [
            LMP_INPUT_DIR / "conf_000.lmp",
            LMP_INPUT_DIR / "input_explore.lammps",
            LMP_INPUT_DIR / "input_label.lammps",
            LMP_INPUT_DIR / "colvar",
            RID_CONFIG,
            MACHINE_CONFIG,
        ]
        for path in required_files:
            self.assertTrue(path.exists(), msg=f"missing {path}")

    def test_rid_config_uses_lammps_and_custom_cv(self):
        with open(RID_CONFIG, "r") as handle:
            rid_config = json.load(handle)
        self.assertEqual(rid_config["ExploreMDConfig"]["type"], "lmp")
        self.assertEqual(rid_config["LabelMDConfig"]["type"], "lmp")
        self.assertEqual(rid_config["LabelMDConfig"]["method"], "restrained")
        self.assertEqual(rid_config["CV"]["mode"], "custom")
        self.assertEqual(rid_config["SelectorConfig"]["slice_mode"], "dpdata")

    def test_lammps_run_command(self):
        with open(RID_CONFIG, "r") as handle:
            rid_config = json.load(handle)
        explore_cmd = get_mdrun_cmd(
            sampler_type="lmp",
            inputfile=rid_config["ExploreMDConfig"]["inputfile"],
        )
        label_cmd = get_mdrun_cmd(
            sampler_type="lmp",
            inputfile=rid_config["LabelMDConfig"]["inputfile"],
        )
        self.assertEqual(
            explore_cmd,
            ["lmp_serial", "-i", "input_explore.lammps"],
        )
        self.assertEqual(
            label_cmd,
            ["lmp_serial", "-i", "input_label.lammps"],
        )

    def test_build_lmp_dict_copies_conf(self):
        conf_path = LMP_INPUT_DIR / "conf_000.lmp"
        task_files = build_lmp_dict(str(conf_path))
        self.assertIn(lmp_conf_name, task_files)
        with open(conf_path, "r") as handle:
            conf_content = handle.read()
        self.assertEqual(task_files[lmp_conf_name][0], conf_content)


if __name__ == "__main__":
    unittest.main()
