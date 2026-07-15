from typing import Dict, List, Union
from dflow.plugins.lebesgue import LebesgueExecutor
from dflow.plugins.dispatcher import DispatcherExecutor
from dflow import SlurmRemoteExecutor
import os


def init_executor(
        executor_dict,
    ):
    if executor_dict is None:
        return None
    if "type" in executor_dict:
        etype = executor_dict.pop('type')
        if etype.lower() == "lebesgue_v2":
            return LebesgueExecutor(**executor_dict)
        elif etype.lower() == "slurm":
            return SlurmRemoteExecutor(**executor_dict)
        else:
            raise RuntimeError('unknown executor type', etype)    
    elif "machine_dict" in executor_dict:
        return DispatcherExecutor(**executor_dict)
    else:
        raise RuntimeError('unknown executor dict')   


def normalize_std_threshold(
        threshold: Union[float, int, List[Union[float, int]]],
        cv_dim: int,
    ) -> List[float]:
    """Normalize label std thresholds to a per-CV list."""
    if isinstance(threshold, (int, float)):
        return [float(threshold)] * cv_dim
    if isinstance(threshold, list):
        if len(threshold) == 0:
            raise ValueError("std_threshold list must not be empty")
        if len(threshold) == 1:
            return [float(threshold[0])] * cv_dim
        if len(threshold) != cv_dim:
            raise ValueError(
                f"std_threshold length {len(threshold)} != cv_dim {cv_dim}"
            )
        return [float(value) for value in threshold]
    raise TypeError("std_threshold must be a float or list of floats")


def normalize_resources(config_dict: Dict):
    template_dict = {}
    template_dict["template_config"] = config_dict.get("template_config", {})
    template_dict["executor"] = config_dict.get("executor", None)
    if template_dict["executor"] is None:
        assert ("image" in template_dict["template_config"].keys()) and \
            template_dict["template_config"]["image"] is not None
    elif template_dict["executor"] is not None and not "type" in template_dict["executor"]:
        return template_dict
    elif template_dict["executor"] is not None and template_dict["executor"]["type"] == "slurm":
        header_list = template_dict["executor"]["header"]
        template_dict["executor"]["header"] = "\n".join(header_list)
    return template_dict
