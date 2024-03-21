from .gym_env import GymEnv
from .game_envs import EnvType, BasicFlappyEnv, EnemyCloudskimmerEnv, AdvancedFlappyEnv


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
