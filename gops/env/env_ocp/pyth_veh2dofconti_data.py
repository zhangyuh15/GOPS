#  Copyright (c). All Rights Reserved.
#  General Optimal control Problem Solver (GOPS)
#  Intelligent Driving Lab(iDLab), Tsinghua University
#
#  Creator: iDLab
#  Description: Vehicle 2DOF Model
#  Update Date: 2021-05-55, Congsheng Zhang: create environment
#  Update Date: 2022-09-21, Jiaxin Gao: change to tracking problem

import gym
from gym.utils import seeding
import numpy as np
from gym.wrappers.time_limit import TimeLimit

class VehicleDynamics(object):
    def __init__(self, **kwargs):
        self.vehicle_params = dict(k_f=-128915.5,  # front wheel cornering stiffness [N/rad]
                                   k_r=-85943.6,  # rear wheel cornering stiffness [N/rad]
                                   l_f=1.06,  # distance from CG to front axle [m]
                                   l_r=1.85,  # distance from CG to rear axle [m]
                                   m=1412.,  # mass [kg]
                                   I_z=1536.7,  # Polar moment of inertia at CG [kg*m^2]
                                   miu=1.0,  # tire-road friction coefficient
                                   g=9.81,  # acceleration of gravity [m/s^2]
                                   u=10.)
        l_f, l_r, mass, g = self.vehicle_params['l_f'], self.vehicle_params['l_r'], \
                        self.vehicle_params['m'], self.vehicle_params['g']
        F_zf, F_zr = l_r * mass * g / (l_f + l_r), l_f * mass * g / (l_f + l_r)
        self.vehicle_params.update(dict(F_zf=F_zf,
                                        F_zr=F_zr))
        self.path = ReferencePath()
        self.prediction_horizon = kwargs["predictive_horizon"]

    def f_xu(self, states, actions, delta_t):
        y, phi, v, w = states[0], states[1], states[2], states[3]
        steer = actions[0]
        u = self.vehicle_params['u']
        k_f = self.vehicle_params['k_f']
        k_r = self.vehicle_params['k_r']
        l_f = self.vehicle_params['l_f']
        l_r = self.vehicle_params['l_r']
        m = self.vehicle_params['m']
        I_z = self.vehicle_params['I_z']
        next_state = np.stack([y + delta_t * (u * phi + v),
                      phi + delta_t * w,
                    (m * v * u + delta_t * (l_f * k_f - l_r * k_r) * w - delta_t * k_f * steer * u - delta_t * m * np.square(u) * w) / (m * u - delta_t * (k_f + k_r)),
                    (I_z * w * u + delta_t * (l_r * k_f - l_r * k_r) * v - delta_t * l_f * k_f * steer * u) / (I_z * u - delta_t * (np.square(l_f) * k_f + np.square(l_r) * k_r))
                      ])
        return next_state

    def prediction(self, x_1, u_1, frequency):
        x_next = self.f_xu(x_1, u_1, 1 / frequency)
        return x_next

    def simulation(self, state, action, frequency, ref_num, t):
        state_next = self.prediction(state, action, frequency)
        y, phi, v, w = state_next[0], state_next[1], state_next[2], state_next[3]
        path_y, path_phi = self.path.compute_path_y(t, ref_num), \
                           self.path.compute_path_phi(t, ref_num)
        obs = np.array([y - path_y, phi - path_phi, v, w], dtype=np.float32)
        for i in range(self.prediction_horizon - 1):
            ref_y = self.path.compute_path_y(t + (i + 1) / frequency, ref_num)
            ref_phi = self.path.compute_path_phi(t + (i + 1) / frequency, ref_num)
            ref_obs = np.array([y - ref_y, phi - ref_phi], dtype=np.float32)
            obs = np.hstack((obs, ref_obs))
        if state_next[3] > np.pi:
            state_next[3] -= 2 * np.pi
        if state_next[3] <= -np.pi:
            state_next[3] += 2 * np.pi
        return state_next, obs

    def compute_rewards(self, obs, actions):  # obses and actions are tensors
        v_ys, rs, delta_ys, delta_phis = obs[0], obs[1], obs[2], obs[3]
        devi_y = -np.square(delta_ys)
        devi_phi = -np.square(delta_phis)
        steers = actions[0]
        punish_yaw_rate = -np.square(rs)
        punish_steer = -np.square(steers)
        punish_vys = - np.square(v_ys)
        rewards = 2.0 * devi_y + 0.1 * devi_phi + 0.2 * punish_yaw_rate + 5 * punish_steer + 0.1 * punish_vys
        return rewards


class ReferencePath(object):
    def __init__(self):
        self.expect_v = 10

    def compute_path_x(self, t, num):
        x = np.zeros_like(t)
        if num == 0:
            x = 10 * t + np.cos(2 * np.pi * t / 6)
        elif num == 1:
            x = self.expect_v * t
        return x

    def compute_path_y(self, t, num):
        y = np.zeros_like(t)
        if num == 0:
            y = 1.5 * np.sin(2 * np.pi * t / 10)
        elif num == 1:
            if t <= 5:
                y = 0
            elif t <= 9:
                y = 0.875 * t - 4.375
            elif t <= 14:
                y = 3.5
            elif t <= 18:
                y = -0.875 * t + 15.75
            elif t > 18:
                y = 0
        return y

    def compute_path_phi(self, t, num):
        phi = np.zeros_like(t)
        if num == 0:
            phi = (1.5 * np.sin(2 * np.pi * (t + 0.001) / 10) - 1.5 * np.sin(2 * np.pi * t / 10))\
                  / (10 * t + np.cos(2 * np.pi * (t + 0.001) / 6) - 10 * t + np.cos(2 * np.pi * t / 6))
        elif num == 1:
            if t <= 5:
                phi = 0
            elif t <= 9:
                phi = ((0.875 * (t + 0.001) - 4.375) - (0.875 * t - 4.375)) \
                      / (self.expect_v * 0.001)
            elif t <= 14:
                phi = 0
            elif t <= 18:
                phi = ((-0.875 * (t + 0.001) + 15.75) - (-0.875 * t + 15.75)) \
                      / (self.expect_v * 0.001)
            elif t > 18:
                phi = 0

        return np.arctan(phi)


class SimuVeh2dofconti(gym.Env,):
    def __init__(self, num_future_data=0, num_agent=1, **kwargs):
        self.is_adversary = kwargs.get("is_adversary", False)
        self.is_constraint = kwargs.get("is_constraint", False)
        self.prediction_horizon = kwargs["predictive_horizon"]
        self.vehicle_dynamics = VehicleDynamics(**kwargs)
        self.num_agent = num_agent
        self.base_frequency = 10
        self.expected_vs = 10.
        self.observation_space = gym.spaces.Box(
            low=np.array([-np.inf] * (22)),
            high=np.array([np.inf] * (22)),
            dtype=np.float32)
        self.action_space = gym.spaces.Box(low=np.array([-np.pi / 6]),
                                           high=np.array([np.pi / 6]),
                                           dtype=np.float32)
        self.obs = None
        self.state = None
        self.state_dim = 4
        self.ref_num = None
        self.t = None
        self.info_dict = {
            "state": {"shape": self.state_dim, "dtype": np.float32},
            "ref_num": {"shape": (), "dtype": np.uint8},
            "t": {"shape": (), "dtype": np.uint8},
        }
        self.seed()

    @property
    def additional_info(self):
        return self.info_dict

    def seed(self, seed=None):
        self.np_random, seed = seeding.np_random(seed)
        return [seed]

    def reset(self, init_state=None, t=None, ref_num=None):
        init_y = None
        init_phi = None
        init_v = None
        init_w = None
        obs = None
        if (init_state == None) & (t == None) & (ref_num == None):
            flag = [0, 1]
            self.ref_num = self.np_random.choice(flag)
            t = 20. * self.np_random.uniform(low=0., high=1.)
            self.t = t
            init_delta_y = self.np_random.normal(0, 1)
            init_y = self.vehicle_dynamics.path.compute_path_y(t, self.ref_num) + init_delta_y
            init_delta_phi = self.np_random.normal(0, np.pi / 9)
            init_phi = self.vehicle_dynamics.path.compute_path_phi(t, self.ref_num) + init_delta_phi
            beta = self.np_random.normal(0, 0.15)
            init_v = self.expected_vs * np.tan(beta)
            init_w = self.np_random.normal(0, 0.3)
            obs = np.array([init_delta_y, init_delta_phi, init_v, init_w], dtype=np.float32)
        elif (init_state != None) & (t != None) & (ref_num != None):
            flag = [0, 1]
            self.ref_num = self.np_random.choice(flag)
            self.t = t
            init_y, init_phi, init_v, init_w = init_state[0], init_state[1], init_state[2], init_state[3]
            init_delta_y = self.vehicle_dynamics.path.compute_path_y(t, self.ref_num) - init_y
            init_delta_phi = self.vehicle_dynamics.path.compute_path_phi(t, self.ref_num) + init_phi
            obs = np.array([init_delta_y, init_delta_phi, init_v, init_w], dtype=np.float32)
        else:
            print("reset error")

        for i in range(self.prediction_horizon - 1):
            ref_y = self.vehicle_dynamics.path.compute_path_y(t + (i + 1) / self.base_frequency, self.ref_num)
            ref_phi = self.vehicle_dynamics.path.compute_path_phi(t + (i + 1) / self.base_frequency, self.ref_num)
            ref_obs = np.array([init_y - ref_y, init_phi - ref_phi], dtype=np.float32)
            obs = np.hstack((obs, ref_obs))
        self.obs = obs
        self.state = np.array([init_y, init_phi, init_v, init_w], dtype=np.float32)
        return self.obs

    def step(self, action: np.ndarray, adv_action=None):  # think of action is in range [-1, 1]
        steer_norm = action
        action = steer_norm * 1.2 * np.pi / 9
        reward = self.vehicle_dynamics.compute_rewards(self.obs, action)
        self.state, self.obs = self.vehicle_dynamics.simulation(self.state, action,
                                             self.base_frequency, self.ref_num, self.t)
        self.done = self.judge_done(self.state, self.t)
        state = np.array(self.state, dtype=np.float32)
        y_ref = self.vehicle_dynamics.path.compute_path_y(self.t, self.ref_num)
        info = {
            "state": state,
            "t": self.t,
            "ref": [y_ref, None, None, None],
            "ref_num": self.ref_num,
        }

        return self.obs, reward, self.done, info

    def judge_done(self, state, t):
        y, phi, v, w = state[0], state[1], state[2], state[3]

        done = (np.abs(y - self.vehicle_dynamics.path.compute_path_y(t, self.ref_num)) > 3) | \
               (np.abs(phi - self.vehicle_dynamics.path.compute_path_phi(t, self.ref_num)) > np.pi / 4.)
        return done

    def close(self):
        pass

    def render(self, mode='human'):
        pass


def env_creator(**kwargs):
    """
    make env `pyth_veh2dofconti`
    """
    return TimeLimit(SimuVeh2dofconti(**kwargs), 200)

if __name__ == "__main__":
    env = env_creator()
    env.seed()
    env.reset()
    for _ in range(100):
        action = env.action_space.sample()
        s, r, d, _ = env.step(action)
        print(s)
        # env.render()
        if d: env.reset()