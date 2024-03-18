import gymnasium as gym
import numpy as np
from enum import Enum

from ..flappybird import FlappyBird
from ..utils import printc


class EnvType(Enum):
    BASIC_FLAPPY = "basic_flappy"
    ADVANCED_FLAPPY = "advanced_flappy"
    ENEMY_CLOUDSKIMMER = "enemy_cloudskimmer"
    ENEMY_AEROTHIEF = "enemy_aerothief"


class BaseEnv(gym.Env):
    metadata = {'render_modes': ['human']}  # this probably won't be used

    def __init__(self):
        super().__init__()

        self.game = FlappyBird()
        self.game.init_env()

        self.set_action_and_observation_space()

    def step(self, action):
        observation, reward, terminated, truncated = self.perform_step(action)
        info = {}  # populate with additional info if necessary

        # if reward > 5:
        #     print(reward)

        observation = np.clip(observation, self.observation_space.low, self.observation_space.high)  # TODO should we clip or not?

        return observation, reward, terminated, truncated, info

    def reset(self, *, seed: int | None = None, options: dict | None = None) -> tuple[np.ndarray, dict]:
        if seed or options:
            printc("WARNING: Seed and options are not supported in FlappyBird() yet.", color='yellow')

        self.game.reset_env()

        game_state = self.get_state()
        info = {}

        return game_state, info

    def render(self):
        # rendering is handled by the game itself
        pass

    def close(self):
        self.game = None

    def get_state(self):
        raise NotImplementedError("get_state() method must be implemented in the subclass")

    def perform_step(self, action):
        raise NotImplementedError("perform_step() method must be implemented in the subclass")

    def set_action_and_observation_space(self):
        raise NotImplementedError("set_action_and_observation_space() method must be implemented in the subclass")


class BasicFlappyEnv(BaseEnv):
    def get_state(self):
        return self.game.get_state_basic_flappy()

    def perform_step(self, action):
        return self.game.step_basic_flappy(action)

    def set_action_and_observation_space(self):
        # self.action_space = gym.spaces.MultiDiscrete([2, 3])  # for multiple actions
        self.action_space = gym.spaces.Discrete(2)  # 0: do nothing, 1: flap the wings
        self.observation_space = gym.spaces.Box(
            # low=np.array([-120, -15, -90, -265, 200, 125, 200, 515, 200, 905, 200], dtype=np.float32),
            # high=np.array([755, 19, 20, 300, 600, 510, 600, 900, 600, 1290, 600], dtype=np.float32),
            low=np.array([-120, -17, 0, -650, -650], dtype=np.float32),
            high=np.array([755, 21, 500, 550, 550], dtype=np.float32),
            dtype=np.float32
        )


class AdvancedFlappyEnv(BaseEnv):
    def get_state(self):
        return self.game.get_state_advanced_flappy()

    def perform_step(self, action):
        return self.game.step_advanced_flappy(action)

    def set_action_and_observation_space(self):
        # TODO implement this
        pass


class EnemyCloudskimmerEnv(BaseEnv):
    def get_state(self):
        return self.game.get_state_enemy_cloudskimmer()

    def perform_step(self, action):
        return self.game.step_enemy_cloudskimmer(action)

    def set_action_and_observation_space(self):
        # TODO implement this
        pass


class EnemyAerothiefEnv(BaseEnv):
    def get_state(self):
        pass
        # return self.game.get_state_enemy_aerothief()

    def perform_step(self, action):
        pass
        # return self.game.step_enemy_aerothief(action)

    def set_action_and_observation_space(self):
        # TODO implement this
        pass


class FlappyBirdEnvManager:
    map_env_to_class = {
        EnvType.BASIC_FLAPPY: BasicFlappyEnv,
        EnvType.ADVANCED_FLAPPY: AdvancedFlappyEnv,
        EnvType.ENEMY_CLOUDSKIMMER: EnemyCloudskimmerEnv,
        EnvType.ENEMY_AEROTHIEF: EnemyAerothiefEnv
    }

    def __init__(self, env_type: EnvType = EnvType.BASIC_FLAPPY):
        self.env = self.map_env_to_class[env_type]()

    def get_env(self):
        return self.env

    def test_env(self):
        for _ in range(10_000):
            action = self.env.action_space.sample()  # take a random action
            obs, reward, terminated, truncated, info = self.env.step(action)

            if terminated or truncated:
                self.env.reset()
