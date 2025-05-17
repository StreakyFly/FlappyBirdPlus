from typing import Type, Callable, Optional

from .base_env import BaseEnv
from .env_types import EnvType
from .gym_env import GymEnv


class EnvManager:
    def __init__(self, env_type: EnvType):
        map_env_to_getclass_method: dict[EnvType, Callable[[], Type[BaseEnv]]] = {
            EnvType.BASIC_FLAPPY: self.get_basic_flappy_env_class,
            EnvType.ADVANCED_FLAPPY: self.get_advanced_flappy_env_class,
            EnvType.ENEMY_CLOUDSKIMMER: self.get_enemy_cloudskimmer_env_class,
            # EnvType.ENEMY_AEROTHIEF: self.get_enemy_aerothief_env_class,
        }

        self.env_class: Type[BaseEnv] = map_env_to_getclass_method.get(env_type)()
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

        for _ in range(10_000):
            action = self.env.action_space.sample()  # take a random action
            obs, reward, terminated, truncated, info = self.env.step(action)

            if terminated or truncated:
                self.env.reset()

    @staticmethod
    def get_basic_flappy_env_class() -> Type[BaseEnv]:
        from .basic_flappy_env import BasicFlappyEnv
        return BasicFlappyEnv

    @staticmethod
    def get_advanced_flappy_env_class() -> Type[BaseEnv]:
        from .advanced_flappy_env import AdvancedFlappyEnv
        return AdvancedFlappyEnv

    @staticmethod
    def get_enemy_cloudskimmer_env_class() -> Type[BaseEnv]:
        from .enemy_cloudskimmer_env import EnemyCloudSkimmerEnv
        return EnemyCloudSkimmerEnv
