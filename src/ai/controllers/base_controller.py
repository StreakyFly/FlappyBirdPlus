import os

import numpy as np
from sb3_contrib import MaskablePPO
from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import DummyVecEnv, VecNormalize

from src.ai.environments import EnvManager, EnvType
from src.config import Config
from src.utils import set_random_seed


class BaseModelController:
    def __init__(self, env_type: EnvType, model_name: str, algorithm: str = 'PPO'):
        root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
        model_path = os.path.join(root_dir, 'ai-models', algorithm, env_type.name.lower(), model_name)
        norm_stats_path = os.path.join(root_dir, 'ai-models', algorithm, env_type.name.lower(), f"{model_name}_normalization_stats.pkl")

        self.dummy_env = DummyVecEnv([lambda: EnvManager(env_type).get_env()])
        self.norm_env = VecNormalize.load(norm_stats_path, self.dummy_env)

        self.model_cls = MaskablePPO if getattr(EnvManager(env_type).get_env_class(), 'requires_action_masking', False) else PPO
        self.model = self.model_cls.load(model_path, env=self.norm_env)

        if Config.handle_seed:
            set_random_seed(Config.seed)  # set random seed after loading the model, to override the model's seed

    def predict_action(self, observation, deterministic=True, use_action_masks=True, entity=None, env=None):
        """
        Predict the action for the given observation using the trained model.
        The observation is normalized before prediction, just like in the training phase.
        """
        normalized_obs = self.norm_env.normalize_obs(observation)

        if use_action_masks:
            # If we move the get_action_masks() logic from the controller to the environment, we can get the action
            #  masks directly from the environment this way. But I think it's best to keep the method in the controller.
            # action_masks = self.norm_env.venv.envs[0].game_env.get_action_masks(entity, env)
            action_masks = self.get_action_masks(entity, env)
            action, _states = self.model.predict(normalized_obs, deterministic=deterministic, action_masks=action_masks)
        else:
            action, _states = self.model.predict(normalized_obs, deterministic=deterministic)

        return action

    @staticmethod
    def perform_action(action, entity, env=None):
        """
        Perform the action on the entity.

        :param action: The action to perform, typically an array of integers.
        :param entity: The entity on which the action will be performed.
        :param env: The environment in which the action is performed (only certain agents require it, e.g. `advanced flappy`).
        """
        raise NotImplementedError("perform_action() method should be implemented in a subclass.")

    @staticmethod
    def get_action_masks(*args) -> np.ndarray:
        """
        Get the action masks for the current game state.
        Each mask corresponds to whether an action is feasible (1) or not (0).
        This method is required ONLY if the agent needs action masking.
        """
        raise NotImplementedError("get_action_masks() method should be implemented in a subclass.")
