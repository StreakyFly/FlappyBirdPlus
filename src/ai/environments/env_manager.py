from typing import Type, Callable, Optional

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

        use_action_masking: bool = getattr(self.env_class, 'requires_action_masking', False)

        for _ in range(10_000):
            action = self.env.action_space.sample(tuple(self.env.action_masks()) if use_action_masking else None)  # take a random action
            obs, reward, terminated, truncated, info = self.env.step(action)

            if terminated or truncated:
                self.env.reset()

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
            from .advanced_flappy_env import AdvancedFlappyEnv
            return AdvancedFlappyEnv
        else:
            raise ValueError(f"Invalid env_variant: {env_variant}. ADVANCED_FLAPPY supports [MAIN] only.")

    @staticmethod
    def get_enemy_cloudskimmer_env_class(env_variant: EnvVariant) -> Type[BaseEnv]:
        if env_variant == EnvVariant.MAIN:
            from src.ai.environments.enemy_cloudskimmer.enemy_cloudskimmer_main_env import EnemyCloudSkimmerEnv
            return EnemyCloudSkimmerEnv
        elif env_variant == EnvVariant.SIMPLE:
            from src.ai.environments.enemy_cloudskimmer.enemy_cloudskimmer_simple_env import EnemyCloudskimmerSimpleEnv
            return EnemyCloudskimmerSimpleEnv
        else:
            raise ValueError(f"Invalid env_variant: {env_variant}. ENEMY_CLOUDSKIMMER supports [MAIN, STATIC] only.")
