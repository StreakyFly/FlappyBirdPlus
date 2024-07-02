import gymnasium as gym
import numpy as np

from .environments import BaseEnv
from ..utils import printc


class GymEnv(gym.Env):
    metadata = {'render_modes': ['human']}  # this probably won't be used as rendering is handled by the game itself

    def __init__(self, game_env: BaseEnv):
        super().__init__()

        self.game_env = game_env
        # self.game_env.init_env()  # commented this out because I added it in base_env.py

        self.action_space, self.observation_space = self.game_env.get_action_and_observation_space()

    def step(self, action):
        observation, reward, terminated, truncated = self.game_env.perform_step(action)
        info = {}  # populate with additional info if necessary

        # if reward > 5:
        #     print(reward)

        observation = np.clip(observation, self.observation_space.low, self.observation_space.high)  # TODO should we clip or not?

        return observation, reward, terminated, truncated, info

    def reset(self, *, seed: int | None = None, options: dict | None = None) -> tuple[np.ndarray, dict]:
        if seed or options:
            printc("WARNING: Seed and options are not supported in FlappyBird() yet.", color='yellow')

        self.game_env.reset_env()

        game_state = self.game_env.get_state()
        info = {}

        return game_state, info

    def render(self):
        # rendering is handled by the game itself
        pass

    def close(self):
        self.game_env = None
