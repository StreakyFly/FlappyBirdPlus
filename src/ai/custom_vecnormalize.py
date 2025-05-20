from gymnasium import spaces
from stable_baselines3.common.vec_env import VecNormalize, VecEnv

from src.utils import printc


# TODO: DELETE THIS FILE
#  This file is needed for backwards compatibility with the previously trained agents that used it.
#  So basic_flappy and enemy_cloudskimmer trained agents.
#  Once those models are replaced with the new training, this file can be deleted.


class BoxOnlyVecNormalize(VecNormalize):
    """
    VecNormalize raises an error when the observation space is of type spaces.Dict and contains non-Box spaces.
    This class simply fills the norm_obs_keys with only Box space keys if the observation space is a Dict.
    """
    def __init__(self,
                 venv: VecEnv,
                 training: bool = True,
                 norm_obs: bool = True,
                 norm_reward: bool = True,
                 clip_obs: float = 10.0,
                 clip_reward: float = 10.0,
                 gamma: float = 0.99,
                 epsilon: float = 1e-8,
                 ):

        printc("INFO: Keep in mind that only spaces of type spaces.Box will be normalized.", color="blue")

        norm_obs_keys = None
        if isinstance(venv.observation_space, spaces.Dict):
            norm_obs_keys = self.extract_box_keys_from_dict(venv.observation_space)

        super().__init__(venv, training, norm_obs, norm_reward, clip_obs, clip_reward, gamma, epsilon, norm_obs_keys)

    @staticmethod
    def extract_box_keys_from_dict(observation_space):
        """
        Extract keys for *all Box spaces in the Dict observation space.
        *Nested Dict spaces are not supported.
        """
        keys = []
        if isinstance(observation_space, spaces.Dict):
            for key, space in observation_space.spaces.items():
                if isinstance(space, spaces.Box):
                    keys.append(key)
                elif isinstance(space, spaces.Dict):
                    raise ValueError("Nested Dict spaces are not supported.")

        return keys
