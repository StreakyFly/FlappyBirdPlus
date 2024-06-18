import os
from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import DummyVecEnv, VecNormalize

from ..env_manager import EnvManager


class BasicFlappyModelController:
    def __init__(self):
        root_dir = os.path.join(os.path.dirname(__file__), "..", "..", "..")
        model_path = os.path.join(root_dir, "ai-models", "PPO", "basic_flappy", "basic_flappy")
        norm_stats_path = os.path.join(root_dir, "ai-models", "PPO", "basic_flappy", "basic_flappy_normalization_stats.pkl")

        self.dummy_env = DummyVecEnv([lambda: EnvManager().get_env()])
        self.norm_env = VecNormalize.load(norm_stats_path, self.dummy_env)

        self.model = PPO.load(model_path, env=self.norm_env)

    def get_action(self, observation, deterministic=True):
        """
        Predict the action for the given observation using the basic_flappy model.
        The observation is normalized before prediction.
        """
        normalized_obs = self.norm_env.normalize_obs(observation)
        action, _states = self.model.predict(normalized_obs, deterministic=deterministic)
        return action
