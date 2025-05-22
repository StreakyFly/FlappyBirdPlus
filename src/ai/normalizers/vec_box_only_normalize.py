import numpy as np
from gymnasium import spaces
from stable_baselines3.common.vec_env import VecNormalize, VecEnv

from src.utils import printc


class VecBoxOnlyNormalize(VecNormalize):
    """
    VecNormalize raises an error when the observation space is of type spaces.Dict and contains non-Box spaces.
    This class fills the norm_obs_keys with only Box space keys if the observation space is a Dict.
    It also converts some other types of spaces to Box spaces (but does not normalize them) for compatibility
    with VecFrameStack, that requires Box spaces.
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

        printc("[INFO] Keep in mind that ONLY spaces of type Box will be normalized.", color="blue")

        original_space = venv.observation_space
        norm_obs_keys = None  # list of keys to normalize (None means all keys will be normalized)

        if isinstance(original_space, spaces.Dict):
            venv.observation_space, norm_obs_keys = self.preprocess_observation_space(venv.observation_space)  # type: ignore

        super().__init__(venv, training, norm_obs, norm_reward, clip_obs, clip_reward, gamma, epsilon, norm_obs_keys)

    @staticmethod
    def preprocess_observation_space(obs_space: spaces.Dict) -> tuple[spaces.Dict, list[str]]:
        new_spaces = {}
        norm_obs_keys = []

        for key, space in obs_space.spaces.items():
            # Add other types of spaces here if needed
            match space:  # noqa
                case spaces.Box():
                    new_spaces[key] = space
                    norm_obs_keys.append(key)

                case spaces.MultiBinary():
                    new_spaces[key] = spaces.Box(low=0.0, high=1.0, shape=space.shape, dtype=np.float32)
                    printc(f"[INFO] '{key}' (MultiBinary) converted to Box and will NOT be normalized.", color="blue")

                case spaces.Discrete():
                    new_spaces[key] = spaces.Box(low=0.0, high=float(space.n - 1), shape=(1,), dtype=np.float32)
                    printc(f"[INFO] '{key}' (Discrete) converted to Box and will NOT be normalized.", color="blue")

                case spaces.Dict():
                    raise ValueError("Nested Dict spaces are not supported.")

                case _:
                    new_spaces[key] = space
                    printc(f"[INFO] '{key}' ({type(space).__name__}) is not of type Box. It will NOT be normalized.", color="blue")

        return spaces.Dict(new_spaces), norm_obs_keys