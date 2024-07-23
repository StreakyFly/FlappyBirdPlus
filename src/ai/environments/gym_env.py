from typing import Literal

from gymnasium import Env as GymnasiumEnv, spaces
import numpy as np

from .base_env import BaseEnv
from src.utils import printc


class GymEnv(GymnasiumEnv):
    metadata = {'render_modes': ['human']}  # this probably won't be used as rendering is handled by the game env itself

    def __init__(self, game_env: BaseEnv):
        super().__init__()
        # self.game_env.init_env()  # commented this out because I added it in base_env.py

        self.game_env = game_env

        # self.requires_action_masking = getattr(self.game_env, 'requires_action_masking', False)
        # self.action_masks = None
        # https://github.com/Stable-Baselines-Team/stable-baselines3-contrib/issues/49

        self.action_space, self.observation_space = self.game_env.get_action_and_observation_space()

        self.observation_space_clip_modes = self.game_env.get_observation_space_clip_modes()
        self.is_observation_space_of_type_box = isinstance(self.observation_space, spaces.Box)

    def step(self, action):
        observation, reward, terminated, truncated, info = self.game_env.perform_step(action)

        observation = self.clip_observation(observation)

        return observation, reward, terminated, truncated, info

    def reset(self, *, seed: int | None = None, options: dict | None = None) -> tuple[np.ndarray, dict]:
        if seed or options:
            printc("WARNING! Seed and options are not supported in FlappyBird() yet.", color='yellow')

        self.game_env.reset_env()

        observation = self.game_env.get_observation()
        info = {}

        return observation, info

    def render(self):
        # rendering is handled by the game itself
        pass

    def close(self):
        self.game_env = None

    def action_masks(self):
        """
        This method must be named "action_masks".
        In order to use SubprocVecEnv with MaskablePPO, you must implement the action_masks inside the environment.
        https://sb3-contrib.readthedocs.io/en/master/modules/ppo_mask.html
        """
        return self.game_env.get_action_masks()

    def clip_observation(self, observation) -> np.ndarray | dict:
        """
        Clip the observation to the valid range of the observation space or
        raise an error if the observation is out of bounds or
        do nothing with the observation depending on the observation_space_clip_modes.

        Modes:
        -1: raise an error if the observation is out of bounds;
        0: do nothing;
        1: clip the observation to the valid range of the observation space;

        :param observation: the observation to process
        :return: the processed observation
        """

        # if self.observation_space is of type Box
        if self.is_observation_space_of_type_box:
            mode = self.observation_space_clip_modes['box']
            if mode == 1:
                self.observation_space: spaces.Box
                observation = np.clip(observation, self.observation_space.low, self.observation_space.high)
            elif mode == -1:
                if not self.observation_space.contains(observation):
                    raise ValueError(f"Observation {observation} is out of bounds.")
            return observation

        # if self.observation_space is of type Dict
        for key, obs in observation.items():
            self.observation_space: spaces.Dict
            space = self.observation_space[key]
            mode: Literal[-1, 0, 1] = self.observation_space_clip_modes[key]
            if mode == 1:
                if isinstance(space, spaces.Box):
                    observation[key] = np.clip(obs, space.low, space.high)
                elif isinstance(space, spaces.Discrete):
                    observation[key] = np.clip(obs, space.start, space.n - 1)
                elif isinstance(space, spaces.MultiDiscrete):  # TODO ########## not tested if correct yet ##########
                    observation[key] = np.clip(obs, space.start, space.nvec - 1)
                elif isinstance(space, spaces.MultiBinary):
                    observation[key] = np.clip(obs, 0, 1)
                else:
                    raise NotImplementedError(f"Observation space of type '{type(space)}' not implemented yet.")
            elif mode == -1:
                if not space.contains(obs):
                    raise ValueError(f"Invalid {type(space).__name__} observation: {obs}")

        return observation
