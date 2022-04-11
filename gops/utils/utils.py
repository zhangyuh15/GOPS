#  Copyright (c). All Rights Reserved.
#  General Optimal control Problem Solver (GOPS)
#  Intelligent Driving Lab(iDLab), Tsinghua University
#
#  Creator: iDLab
#  Description: Utils Function
#  Update Date: 2021-03-10, Yuhang Zhang: Create codes


import time
import sys
import torch
import torch.nn as nn
import numpy as np
import logging
from typing import Optional

from gops.utils.tensorboard_tools import tb_tags
from gops.utils.action_distributions import *
import random
import importlib

logger = logging.getLogger(__name__)

def get_activation_func(key: str):
    assert isinstance(key, str)

    activation_func = None
    if key == "relu":
        activation_func = nn.ReLU

    elif key == "elu":
        activation_func = nn.ELU

    elif key == "gelu":
        activation_func = nn.GELU

    elif key == "tanh":
        activation_func = nn.Tanh

    elif key == "linear":
        activation_func = nn.Identity

    if activation_func is None:
        print("input activation name:" + key)
        raise RuntimeError

    return activation_func


def get_apprfunc_dict(key: str, type: str, **kwargs):
    var = dict()
    var["apprfunc"] = kwargs[key + "_func_type"]
    var["name"] = kwargs[key + "_func_name"]
    var["obs_dim"] = kwargs["obsv_dim"]
    var["min_log_std"] = kwargs.get(key + "_min_log_std", float("-inf"))
    var["max_log_std"] = kwargs.get(key + "_max_log_std", float("inf"))

    if type == "MLP" or type == "RNN":
        var["hidden_sizes"] = kwargs[key + "_hidden_sizes"]
        var["hidden_activation"] = kwargs[key + "_hidden_activation"]
        var["output_activation"] = kwargs[key + "_output_activation"]
    elif type == "GAUSS":
        var["num_kernel"] = kwargs[key + "_num_kernel"]
    elif type == "CNN":
        var["hidden_activation"] = kwargs[key + "_hidden_activation"]
        var["output_activation"] = kwargs[key + "_output_activation"]
        var["conv_type"] = kwargs[key + "_conv_type"]
    elif type == "CNN_SHARED":
        if key == "feature":
            var["conv_type"] = kwargs["conv_type"]
        else:
            var["feature_net"] = kwargs["feature_net"]
            var["hidden_activation"] = kwargs[key + "_hidden_activation"]
            var["output_activation"] = kwargs[key + "_output_activation"]
    elif type == "POLY":
        var["degree"] = kwargs[key + "_degree"]
    else:
        raise NotImplementedError

    if kwargs["action_type"] == "continu":
        var["act_high_lim"] = kwargs["action_high_limit"]
        var["act_low_lim"] = kwargs["action_low_limit"]
        var["act_dim"] = kwargs["action_dim"]

    else:
        var["act_num"] = kwargs["action_num"]

    if kwargs["policy_act_distribution"] == "default":
        if kwargs["action_type"] == "continu":
            if kwargs["policy_func_name"] == "StochaPolicy":  # todo: add TanhGauss
                var["action_distirbution_cls"] = GaussDistribution
            elif kwargs["policy_func_name"] == "DetermPolicy":
                var["action_distirbution_cls"] = DiracDistribution
        else:
            if kwargs["policy_func_name"] == "StochaPolicyDis":
                var["action_distirbution_cls"] = CategoricalDistribution
            elif kwargs["policy_func_name"] == "DetermPolicyDis":
                var["action_distirbution_cls"] = ValueDiracDistribution
    else:

        var["action_distirbution_cls"] = getattr(
            sys.modules[__name__], kwargs["policy_act_distribution"]
        )

    return var


def change_type(obj):
    if isinstance(
        obj,
        (
            np.int_,
            np.intc,
            np.intp,
            np.int8,
            np.int16,
            np.int32,
            np.int64,
            np.uint8,
            np.uint16,
            np.uint32,
            np.uint64,
        ),
    ):
        return int(obj)
    elif isinstance(obj, (np.float_, np.float16, np.float32, np.float64)):
        return float(obj)
    elif isinstance(obj, (np.ndarray,)):  # add this line
        return obj.tolist()  # add this line
    elif isinstance(obj, dict):
        for k, v in obj.items():
            obj[k] = change_type(v)
        return obj
    elif isinstance(obj, list):
        for i, o in enumerate(obj):
            obj[i] = change_type(o)
        return obj
    else:
        return obj


def random_choice_with_index(obj_list):
    obj_len = len(obj_list)
    random_index = random.choice(list(range(obj_len)))
    random_value = obj_list[random_index]
    return random_value, random_index


def array_to_scalar(arrayLike):
    """Convert size-1 array to scalar"""
    return arrayLike if isinstance(arrayLike, (int, float)) else arrayLike.item()


def seed_everything(seed: Optional[int] = None) -> int:
    max_seed_value = np.iinfo(np.uint32).max
    min_seed_value = np.iinfo(np.uint32).min

    if seed is None:
        seed = random.randint(min_seed_value, max_seed_value)

    elif not isinstance(seed, int):
        seed = int(seed)

    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)

    return seed


def set_seed(trainer_name, seed, offset, env=None):
    """
    When trainer_name is `**_async_**` or `**_sync_**`, set random seed for the subprocess and gym env, 
    else only set the subprocess for gym env

    Parameters
    ----------
    trainer_name : str
        trainer_name
    seed : int
        global seed
    offset : int
        the offset of random seed for the subprocess
    env : gym.Env, optional
        a gym env needs to set random seed, by default None

    Returns
    -------
    (int, gym.Env)
        the random seed for the subprocess, a gym env which the random seed is set
    """

    if trainer_name.split("_")[1] in ["async", "sync"]:
        print("Setting seed of a subprocess to {}".format(seed + offset))
        seed_everything(seed + offset)
        if env is not None:
            env.seed(seed + offset)
        return seed + offset, env

    else:
        if env is not None:
            env.seed(seed)
        return None, env
