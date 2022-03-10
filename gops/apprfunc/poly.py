#  Copyright (c). All Rights Reserved.
#  General Optimal control Problem Solver (GOPS)
#  Intelligent Driving Lab(iDLab), Tsinghua University
#
#  Creator: iDLab
#  Description: Polynomial Approximation Function
#  Update: 2021-03-05, Wenjun Zou: create polynomial function



__all__=['DetermPolicy','StochaPolicy','ActionValue','ActionValueDis','StateValue']


import numpy as np
import torch
import torch.nn as nn
from gops.utils.utils import get_activation_func
from act_distribution_cls import Action_Distribution


def make_features(x, degree=4):
    batch = x.shape[0]
    x = x.unsqueeze(1)
    return torch.cat([x ** i for i in range(0, degree)], 1).reshape(batch, -1)


def count_vars(module):
    return sum([np.prod(p.shape) for p in module.parameters()])


class DetermPolicy(nn.Module, Action_Distribution):
    def __init__(self, **kwargs):
        super().__init__()
        obs_dim = kwargs['obs_dim']
        act_dim = kwargs['act_dim']
        self.degree = 4
        self.pi = nn.Linear(obs_dim*self.degree, act_dim)
        action_high_limit = kwargs['act_high_lim']
        action_low_limit = kwargs['act_low_lim']
        self.register_buffer('act_high_lim', torch.from_numpy(action_high_limit))
        self.register_buffer('act_low_lim', torch.from_numpy(action_low_limit))
        self.action_distirbution_cls = kwargs['action_distirbution_cls']

    def forward(self, obs):
        obs = make_features(obs, self.degree)
        action = (self.act_high_lim-self.act_low_lim)/2 * torch.tanh(self.pi(obs))\
                 + (self.act_high_lim + self.act_low_lim)/2
        return action


class StochaPolicy(nn.Module, Action_Distribution):
    def __init__(self, **kwargs):
        super().__init__()
        obs_dim = kwargs['obs_dim']
        act_dim = kwargs['act_dim']
        action_high_limit = kwargs['act_high_lim']
        action_low_limit = kwargs['act_low_lim']
        self.min_log_std = kwargs['min_log_std']
        self.max_log_std = kwargs['max_log_std']
        self.degree = 4
        self.mean = nn.Linear(obs_dim * self.degree, act_dim)
        self.log_std = nn.Linear(obs_dim * self.degree, act_dim)
        self.register_buffer('act_high_lim', torch.from_numpy(action_high_limit))
        self.register_buffer('act_low_lim', torch.from_numpy(action_low_limit))
        self.action_distirbution_cls = kwargs['action_distirbution_cls']

    def forward(self, obs):
        obs = make_features(obs, self.degree)
        action_mean = self.mean(obs)
        action_std = torch.clamp(self.log_std(obs), self.min_log_std, self.max_log_std).exp()
        return torch.cat((action_mean, action_std), dim=-1)


class ActionValue(nn.Module, Action_Distribution):
    def __init__(self, **kwargs):
        super().__init__()
        obs_dim = kwargs['obs_dim']
        act_dim = kwargs['act_dim']
        self.degree = 2
        self.q = nn.Linear((obs_dim+act_dim) * self.degree, 1)
        self.action_distirbution_cls = kwargs['action_distirbution_cls']

    def forward(self, obs, act):
        input = torch.cat([obs, act], dim=-1)
        input = make_features(input, self.degree)
        q = self.q(input)
        return torch.squeeze(q, -1)


class ActionValueDis(nn.Module, Action_Distribution):
    def __init__(self, **kwargs):
        super().__init__()
        obs_dim  = kwargs['obs_dim']
        act_num = kwargs['act_num']
        self.degree = 2
        self.q = nn.Linear(obs_dim*self.degree, act_num)
        self.action_distirbution_cls = kwargs['action_distirbution_cls']

    def forward(self, obs):
        obs = make_features(obs, self.degree)
        return self.q(obs)


class StochaPolicyDis(ActionValueDis, Action_Distribution):
    pass


class StateValue(nn.Module, Action_Distribution):
    def __init__(self, **kwargs):
        super().__init__()
        obs_dim = kwargs['obs_dim']
        self.degree = 2
        self.v = nn.Linear(obs_dim * self.degree, 1)
        self.action_distirbution_cls = kwargs['action_distirbution_cls']

    def forward(self, obs):
        obs = make_features(obs, self.degree)
        return self.v(obs)
