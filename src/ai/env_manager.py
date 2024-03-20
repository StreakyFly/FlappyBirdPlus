from enum import Enum

from .gym_env import GymEnv
from ..game_envs import BasicFlappyEnv, EnemyCloudskimmerEnv, AdvancedFlappyEnv


class EnvType(Enum):
    BASIC_FLAPPY = "basic_flappy"  # env for training only the basic flappy bird
    ENEMY_CLOUDSKIMMER = "enemy_cloudskimmer"  # env for training the enemy cloudskimmer with basic flappy bird
    ENEMY_AEROTHIEF = "enemy_aerothief"  # env for training the enemy aerothief with basic flappy bird
    ADVANCED_FLAPPY = "advanced_flappy"  # env for training the advanced flappy bird with both enemy agents


class EnvManager:
    map_env_to_class = {
        EnvType.BASIC_FLAPPY: BasicFlappyEnv,
        EnvType.ADVANCED_FLAPPY: AdvancedFlappyEnv,
        EnvType.ENEMY_CLOUDSKIMMER: EnemyCloudskimmerEnv,
        # EnvType.ENEMY_AEROTHIEF: EnemyAerothiefEnv
    }

    def __init__(self, env_type: EnvType = EnvType.BASIC_FLAPPY):
        self.env = GymEnv(self.map_env_to_class[env_type]())

    def get_env(self):
        return self.env

    def test_env(self):
        for _ in range(10_000):
            action = self.env.action_space.sample()  # take a random action
            obs, reward, terminated, truncated, info = self.env.step(action)

            if terminated or truncated:
                self.env.reset()
