import os

from stable_baselines3 import PPO
from sb3_contrib import MaskablePPO
from stable_baselines3.common.vec_env import DummyVecEnv, VecNormalize

from src.ai.environments import EnvManager


class BaseModelController:
    def __init__(self, env_type, model_name, algorithm='PPO'):
        root_dir = os.path.join(os.path.dirname(__file__), "..", "..", "..")
        model_path = os.path.join(root_dir, 'ai-models', algorithm, env_type, model_name)
        norm_stats_path = os.path.join(root_dir, 'ai-models', algorithm, env_type, f"{model_name}_normalization_stats.pkl")

        self.dummy_env = DummyVecEnv([lambda: EnvManager().get_env()])
        self.norm_env = VecNormalize.load(norm_stats_path, self.dummy_env)

        self.model_cls = MaskablePPO if getattr(EnvManager().get_env_class(), 'requires_action_masking', False) else PPO
        self.model = self.model_cls.load(model_path, env=self.norm_env)

    def predict_action(self, observation, deterministic=True, use_action_masks=True, info_for_action_masks=None):
        """
        Predict the action for the given observation using the basic_flappy model.
        The observation is normalized before prediction.
        """
        normalized_obs = self.norm_env.normalize_obs(observation)

        if use_action_masks:
            action, _states = self.model.predict(normalized_obs, deterministic=deterministic, action_mask=self.get_action_masks(info_for_action_masks))
        else:
            action, _states = self.model.predict(normalized_obs, deterministic=deterministic)

        return action

    def perform_action(self, entity, action):
        """
        Perform the action on the entity.
        """
        raise NotImplementedError("perform_action() method should be implemented in a subclass.")

    @staticmethod
    def get_action_masks(*args):
        """
        Computes and returns the action masks.
        This method is only needed if the environment requires action masking.
        """
        raise NotImplementedError("get_action_masks() method should be implemented in a subclass.")
