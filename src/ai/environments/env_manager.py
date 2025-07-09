from typing import Type, Callable, Optional

import numpy as np
from gymnasium.spaces import MultiDiscrete

from .base_env import BaseEnv
from .env_types import EnvType, EnvVariant
from .gym_env import GymEnv


class EnvManager:
    def __init__(self, env_type: EnvType, env_variant: EnvVariant = EnvVariant.MAIN):
        map_env_to_getclass_method: dict[EnvType, Callable[[EnvVariant], Type[BaseEnv]]] = {
            EnvType.BASIC_FLAPPY: self.get_basic_flappy_env_class,
            EnvType.ADVANCED_FLAPPY: self.get_advanced_flappy_env_class,
            EnvType.ENEMY_CLOUDSKIMMER: self.get_enemy_cloudskimmer_env_class,
        }

        self.env_class: Type[BaseEnv] = map_env_to_getclass_method.get(env_type)(env_variant)
        self.env: Optional[GymEnv] = None

    def get_env_class(self) -> Type[BaseEnv]:
        """
        Returns the environment class.
        """
        return self.env_class

    def get_env(self) -> GymEnv:
        """
        Creates the environment instance if it doesn't exist and returns it.
        """
        self.create_env()
        return self.env

    def create_env(self) -> None:
        """
        Creates the environment instance if it doesn't exist.
        """
        if self.env is None:
            self.env = GymEnv(self.env_class())

    def test_env(self) -> None:
        """
        Performs a basic test run of the environment to ensure it behaves as expected.
        """
        self.create_env()
        self.env.reset()  # reset to set the random seed

        use_action_masking: bool = getattr(self.env_class, 'REQUIRES_ACTION_MASKING', False)

        for _ in range(10_000):
            if use_action_masking:
                action_masks = self.format_action_mask(self.env.action_masks(), self.env.action_space)
                action = self.env.action_space.sample(action_masks)  # take a random action
            else:
                action = self.env.action_space.sample()  # take a random action
            obs, reward, terminated, truncated, info = self.env.step(action)

            if terminated or truncated:
                self.env.reset()

    @staticmethod
    def format_action_mask(flat_mask, action_space) -> tuple[np.ndarray, ...]:
        """
        Converts a flat boolean/int action mask into a tuple format suitable for MultiDiscrete sampling.
        Can be extended to support other action spaces in the future.

        :param flat_mask: 1D numpy array of bools/ints.
        :param action_space: The MultiDiscrete action space (e.g. MultiDiscrete([2, 3, 4]))

        return: Tuple of numpy arrays, one for each sub-action dimension.
        """
        # if the mask is already split, return it as is (but as a tuple)
        if flat_mask.ndim > 1:
            return tuple(flat_mask)

        mask = flat_mask

        # handle MultiDiscrete action spaces (for now)
        if isinstance(action_space, MultiDiscrete):
            splits = np.cumsum(action_space.nvec[:-1])
            mask = np.split(flat_mask, splits)

        return tuple(mask)

    @staticmethod
    def get_basic_flappy_env_class(env_variant: EnvVariant) -> Type[BaseEnv]:
        if env_variant == EnvVariant.MAIN:
            from .basic_flappy_env import BasicFlappyEnv
            return BasicFlappyEnv
        else:
            raise ValueError(f"Invalid env_variant: {env_variant}. BASIC_FLAPPY supports [MAIN] only.")

    @staticmethod
    def get_advanced_flappy_env_class(env_variant: EnvVariant) -> Type[BaseEnv]:
        if env_variant == EnvVariant.MAIN:
            from .advanced_flappy.advanced_flappy_main_env import AdvancedFlappyEnv
            return AdvancedFlappyEnv
        else:
            raise ValueError(f"Invalid env_variant: {env_variant}. ADVANCED_FLAPPY supports [MAIN] only.")

    @staticmethod
    def get_enemy_cloudskimmer_env_class(env_variant: EnvVariant) -> Type[BaseEnv]:
        match env_variant:  # noqa
            case EnvVariant.MAIN:
                from .enemy_cloudskimmer.enemy_cloudskimmer_main_env import EnemyCloudSkimmerEnv
                return EnemyCloudSkimmerEnv
            case EnvVariant.STEP1:
                from .enemy_cloudskimmer.enemy_cloudskimmer_step1_env import EnemyCloudSkimmerStep1Env
                return EnemyCloudSkimmerStep1Env
            case EnvVariant.STEP2:
                from .enemy_cloudskimmer.enemy_cloudskimmer_step2_env import EnemyCloudSkimmerStep2Env
                return EnemyCloudSkimmerStep2Env
            case EnvVariant.STEP3:
                from .enemy_cloudskimmer.enemy_cloudskimmer_step3_env import EnemyCloudSkimmerStep3Env
                return EnemyCloudSkimmerStep3Env
            case _:
                raise ValueError(f"Invalid env_variant: {env_variant}. ENEMY_CLOUDSKIMMER supports [MAIN, STEP1, STEP2, STEP3] only.")
