from .gym_env import GymEnv
from .environments import EnvType


class EnvManager:

    def __init__(self, env_type: EnvType = EnvType.BASIC_FLAPPY):
        map_env_to_class = {
            EnvType.BASIC_FLAPPY: self.create_basic_flappy_env,
            EnvType.ADVANCED_FLAPPY: self.create_advanced_flappy_env,
            EnvType.ENEMY_CLOUDSKIMMER: self.create_enemy_cloudskimmer_env,
            # EnvType.ENEMY_AEROTHIEF: EnemyAerothiefEnv
        }

        env_class = map_env_to_class.get(env_type)
        if not env_class:
            raise ValueError(f"Unsupported environment type: {env_type}")

        self.env = GymEnv(env_class())

    def get_env(self):
        """
        Return the current environment instance.
        """
        return self.env

    def test_env(self):
        """
        Perform a basic test run of the environment to ensure it behaves as expected.
        """
        for _ in range(10_000):
            action = self.env.action_space.sample()  # take a random action
            obs, reward, terminated, truncated, info = self.env.step(action)

            if terminated or truncated:
                self.env.reset()

    @staticmethod
    def create_basic_flappy_env():
        from .environments import BasicFlappyEnv
        return BasicFlappyEnv()

    @staticmethod
    def create_advanced_flappy_env():
        from .environments import AdvancedFlappyEnv
        return AdvancedFlappyEnv()

    @staticmethod
    def create_enemy_cloudskimmer_env():
        from .environments import EnemyCloudskimmerEnv
        return EnemyCloudskimmerEnv()

