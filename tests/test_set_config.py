import copy
import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from rid.utils.set_config import (
    DEFAULT_SLICE_GROUP_SIZE,
    DEFAULT_SLICE_POOL_SIZE,
    get_template_slice_config,
    normalize_resources,
)


class TestSetConfig(unittest.TestCase):
    def test_normalize_resources_preserves_slice_config(self):
        resource = {
            "template_config": {"image": "example:latest"},
            "template_slice_config": {"group_size": 6, "pool_size": 2},
        }
        normalized = normalize_resources(resource)
        self.assertEqual(
            normalized["template_slice_config"],
            {"group_size": 6, "pool_size": 2},
        )

    def test_get_template_slice_config_defaults(self):
        config = copy.deepcopy({"template_config": {"image": "example:latest"}})
        slice_config = get_template_slice_config(config)
        self.assertEqual(
            slice_config,
            {
                "group_size": DEFAULT_SLICE_GROUP_SIZE,
                "pool_size": DEFAULT_SLICE_POOL_SIZE,
            },
        )
        self.assertNotIn("template_slice_config", config)

    def test_get_template_slice_config_custom(self):
        config = {
            "template_slice_config": {"group_size": 4, "pool_size": 3},
        }
        slice_config = get_template_slice_config(config)
        self.assertEqual(slice_config, {"group_size": 4, "pool_size": 3})


if __name__ == "__main__":
    unittest.main()
