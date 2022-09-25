#  Copyright (c). All Rights Reserved.
#  General Optimal control Problem Solver (GOPS)
#  Intelligent Driving Lab(iDLab), Tsinghua University
#
#  Creator: Jie Li
#  Description: Aircraft Environment
#

from math import sin, cos
import numpy as np
import gym
from gym import spaces
from gym.utils import seeding
from gym.wrappers.time_limit import TimeLimit
gym.logger.setLevel(gym.logger.ERROR)


class _GymAircraftconti(gym.Env):
    def __init__(self, **kwargs):
        """
        you need to define parameters here
        """
        # define common parameters here
        self.is_adversary = kwargs['is_adversary']
        self.state_dim = 3
        self.action_dim = 1
        self.adversary_dim = 1
        self.tau = 1 / 200  # seconds between state updates

        # define your custom parameters here
        self.A = np.array([[-1.01887, 0.90506, -0.00215],
                           [0.82225, -1.07741, -0.17555],
                           [0, 0, -1]], dtype=np.float32)
        self.A_attack_ang = np.array([-1.01887, 0.90506, -0.00215], dtype=np.float32).reshape((3, 1))
        self.A_rate = np.array([0.82225, -1.07741, -0.17555], dtype=np.float32).reshape((3, 1))
        self.A_elevator_ang = np.array([0, 0, -1], dtype=np.float32).reshape((3, 1))
        self.B = np.array([0., 0., 1.]).reshape((3, 1))
        self.D = np.array([1., 0., 0.]).reshape((3, 1))

        # utility information
        self.Q = np.eye(self.state_dim)
        self.R = np.eye(self.action_dim)
        self.gamma = 1
        self.gamma_atte = kwargs['gamma_atte']

        # state & action space
        self.fixed_initial_state = kwargs['fixed_initial_state']  # for env_data & on_sampler
        self.initial_state_range = kwargs['initial_state_range']  # for env_model
        self.attack_ang_initial = self.initial_state_range[0]
        self.rate_initial = self.initial_state_range[1]
        self.elevator_ang_initial = self.initial_state_range[2]
        self.state_threshold = kwargs['state_threshold']
        self.attack_ang_threshold = self.state_threshold[0]
        self.rate_threshold = self.state_threshold[1]
        self.elevator_ang_threshold = self.state_threshold[2]
        self.max_action = [1.0]
        self.min_action = [-1.0]
        self.max_adv_action = [1.0 / self.gamma_atte]
        self.min_adv_action = [-1.0 / self.gamma_atte]

        self.observation_space = spaces.Box(low=np.array([-self.attack_ang_threshold, -self.rate_threshold, -self.elevator_ang_threshold]),
                                            high=np.array([self.attack_ang_threshold, self.rate_threshold, self.elevator_ang_threshold]),
                                            shape=(3,)
                                            )
        # self.action_space = spaces.Box(low=np.array(self.min_action + self.min_adv_action),
        #                                high=np.array(self.max_action + self.max_adv_action),
        #                                shape=(2,)
        #                                )
        self.action_space = spaces.Box(low=np.array(self.min_action),
                                       high=np.array(self.max_action),
                                       shape=(1,)
                                       )

        self.seed()
        self.viewer = None
        self.state = None

        self.steps_beyond_done = None

        self.max_episode_steps = kwargs['max_episode_steps']  # original = 200
        self.steps = 0

    def seed(self, seed=None):
        self.np_random, seed = seeding.np_random(seed)
        return [seed]

    def stepPhysics(self, action, adv_action):

        tau = self.tau
        A = self.A
        attack_ang, rate, elevator_ang = self.state
        elevator_vol = action[0]  # the elevator actuator voltage
        wind_attack_angle = adv_action[0]  # wind gusts on angle of attack

        attack_ang_dot = A[0, 0] * attack_ang + A[0, 1] * rate + A[0, 2] * elevator_ang + wind_attack_angle
        rate_dot = A[1, 0] * attack_ang + A[1, 1] * rate + A[1, 2] * elevator_ang
        elevator_ang_dot = A[2, 0] * attack_ang + A[2, 1] * rate + A[2, 2] * elevator_ang + elevator_vol

        next_attack_ang = attack_ang_dot * tau + attack_ang
        next_rate = rate_dot * tau + rate
        next_elevator_angle = elevator_ang_dot * tau + elevator_ang
        return next_attack_ang, next_rate, next_elevator_angle

    def step(self, inputs):
        action = inputs[:self.action_dim]
        adv_action = inputs[self.action_dim:]
        if not adv_action or adv_action is None:
            adv_action = [0]

        attack_ang, rate, elevator_ang = self.state
        self.state = self.stepPhysics(action, adv_action)
        next_attack_ang, next_rate, next_elevator_angle = self.state
        done = next_attack_ang < -self.attack_ang_threshold or next_attack_ang > self.attack_ang_threshold \
            or next_rate < -self.rate_threshold or next_rate > self.rate_threshold \
            or next_elevator_angle < -self.elevator_ang_threshold or next_elevator_angle > self.elevator_ang_threshold
        done = bool(done)

        # -----------------
        self.steps += 1
        if self.steps >= self.max_episode_steps:
            done = True
        # ---------------

        if not done:
            reward = self.Q[0][0] * attack_ang ** 2 + self.Q[1][1] * rate ** 2 + self.Q[2][2] * elevator_ang ** 2 \
                     + self.R[0][0] * action[0] ** 2 - self.gamma_atte ** 2 * adv_action[0] ** 2
        elif self.steps_beyond_done is None:
            # Pole just fell!
            self.steps_beyond_done = 0
            reward = self.Q[0][0] * attack_ang ** 2 + self.Q[1][1] * rate ** 2 + self.Q[2][2] * elevator_ang ** 2 \
                     + self.R[0][0] * action[0] ** 2 - self.gamma_atte ** 2 * adv_action[0] ** 2
        else:
            if self.steps_beyond_done == 0:
                gym.logger.warn("""
You are calling 'step()' even though this environment has already returned
done = True. You should always call 'reset()' once you receive 'done = True'
Any further steps are undefined behavior.
                """)
            self.steps_beyond_done += 1
            reward = 0.0

        return np.array(self.state), reward, done, {}

    @staticmethod
    def exploration_noise(time):
        n = sin(time)**2 * cos(time) + sin(2 * time)**2 * cos(0.1 * time) + sin(1.2 * time)**2 * cos(0.5 * time) \
            + sin(time)**5 + sin(1.12 * time)**2 + sin(2.4 * time)**3 * cos(2.4 * time)
        return np.array([n, 0])

    def reset(self):  # for on_sampler
        self.state = self.fixed_initial_state
        self.steps_beyond_done = None
        self.steps = 0
        return np.array(self.state)

    def render(self, mode='human'):
        pass

    def close(self):
        if self.viewer:
            self.viewer.close()


def env_creator(**kwargs):
    return TimeLimit(_GymAircraftconti(**kwargs), _GymAircraftconti(**kwargs).max_episode_steps)  # original = 200


if __name__ == '__main__':
    pass
