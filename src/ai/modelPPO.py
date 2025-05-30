import os
import time
from typing import Type

from gymnasium import spaces
from sb3_contrib import MaskablePPO
# from sb3_contrib.common.maskable.callbacks import MaskableEvalCallback
from sb3_contrib.common.maskable.evaluation import evaluate_policy as maskable_evaluate_policy
from stable_baselines3 import PPO
from stable_baselines3.common.callbacks import CheckpointCallback
from stable_baselines3.common.env_util import make_vec_env
from stable_baselines3.common.evaluation import evaluate_policy as normal_evaluate_policy
from stable_baselines3.common.vec_env import VecNormalize, VecEnv, SubprocVecEnv

from src.utils import printc
from .environments import EnvManager
from .environments.base_env import BaseEnv
from .training_config import TrainingConfig


# TODO Action masking hasn't been tested yet, so it's possible that it hasn't been implemented properly.
#  Some necessary adjustments might be missing, so if something isn't working properly, the issue is
#  probably somewhere in this file.
#  Docs: https://sb3-contrib.readthedocs.io/en/master/modules/ppo_mask.html


class ModelPPO:
    def __init__(self, env_type=None, run_id=None) -> None:
        self.env_type = env_type
        self.model_name = self.env_type.value
        self.run_id = run_id or self._generate_run_id()

        env_class: Type[BaseEnv] = EnvManager(self.env_type).get_env_class()
        self.training_config: TrainingConfig = env_class.get_training_config()
        self.use_action_masking = getattr(env_class, 'requires_action_masking', False)
        self.model_cls = MaskablePPO if self.use_action_masking else PPO

        self.checkpoints_dir = None
        self.tensorboard_dir = None
        self.final_model_path = None
        self.norm_stats_path = None

        self._initialize_directories()

    @staticmethod
    def _generate_run_id() -> str:
        return f"run_{time.strftime('%Y%m%d_%H%M%S')}"

    def _initialize_directories(self) -> None:
        base_dir = os.path.join('ai-models', 'PPO', self.env_type.value)
        run_dir = os.path.join(base_dir, self.run_id)
        self.checkpoints_dir = os.path.join(run_dir, 'checkpoints')
        self.tensorboard_dir = os.path.join(run_dir, 'tensorboard_logs')
        self.final_model_path = os.path.join(run_dir, self.env_type.value)
        self.norm_stats_path = os.path.join(run_dir, self.env_type.value + '_normalization_stats.pkl')
        os.makedirs(run_dir, exist_ok=True)
        os.makedirs(self.checkpoints_dir, exist_ok=True)
        os.makedirs(self.tensorboard_dir, exist_ok=True)

    def train(self, norm_env=None, model=None, continue_training: bool = False) -> None:
        if norm_env is None:
            env = self._create_environments(n_envs=6, use_subproc_vec_env=True)
            norm_env = self.training_config.normalizer(env, norm_obs=True, norm_reward=True, clip_obs=self.training_config.clip_norm_obs)

        if model is None:
            policy = 'MultiInputPolicy' if isinstance(norm_env.observation_space, spaces.Dict) else 'MlpPolicy'
            # create the model using the normalized environment; use cpu as it's faster than gpu in this case
            model = self.model_cls(
                policy, norm_env, verbose=1, device='cpu', tensorboard_log=self.tensorboard_dir,
                learning_rate=self.training_config.learning_rate,
                n_steps=self.training_config.n_steps,
                batch_size=self.training_config.batch_size,
                gamma=self.training_config.gamma,
                clip_range=self.training_config.clip_range,
                policy_kwargs=self.training_config.policy_kwargs,
            )

        if continue_training:
            model._last_obs = None  # TODO Is this necessary? If not, remove it.

        # save the model & normalization statistics every N steps
        checkpoint_callback = CheckpointCallback(
            save_freq=self.training_config.save_freq,  # this number is basically multiplied by n_envs
            save_path=self.checkpoints_dir,
            name_prefix=self.model_name,
            save_vecnormalize=True)

        # train the model
        model.learn(
            total_timesteps=self.training_config.total_timesteps,
            tb_log_name=self.model_name,
            callback=checkpoint_callback,
            reset_num_timesteps=not continue_training)

        # save the final model & the normalization statistics
        model.save(self.final_model_path)
        norm_env.save(self.norm_stats_path)

    def continue_training(self) -> None:
        env = self._create_environments(n_envs=6, use_subproc_vec_env=True)
        norm_env = self._load_normalization_stats(path=self.norm_stats_path, env=env)
        model = self._load_model(self.final_model_path, env=norm_env)

        self.train(norm_env, model, continue_training=True)

    def run(self) -> None:
        env = self._create_environments(n_envs=1, use_subproc_vec_env=False)
        norm_env = self._load_normalization_stats(path=self.norm_stats_path, env=env, for_training=False)
        model = self._load_model(self.final_model_path, env=norm_env)

        obs = norm_env.reset()
        while True:
            if self.use_action_masking:
                action_masks = env.envs[0].env.action_masks()  # ಠ_ಠ
                action, _ = model.predict(obs, deterministic=True, action_masks=action_masks)
            else:
                action, _ = model.predict(obs, deterministic=True)
            obs, _, done, _ = norm_env.step(action)
            if done:
                obs = norm_env.reset()

    def evaluate(self) -> None:
        env = self._create_environments(n_envs=6, use_subproc_vec_env=True)
        norm_env = self._load_normalization_stats(path=self.norm_stats_path, env=env, for_training=False)
        model = self._load_model(self.final_model_path, env=norm_env)

        printc("WARNING! Each episode ends after termination. "
               "If termination never happens, the episode will never end.", color="yellow")

        evaluate_policy = maskable_evaluate_policy if self.use_action_masking else normal_evaluate_policy
        mean_reward, std_reward = evaluate_policy(model, model.get_env(), n_eval_episodes=10,
                                                       deterministic=True, reward_threshold=None)
        print(f"mean_reward: {mean_reward: .2f} +/- {std_reward: .2f}")
        norm_env.close()

    def _create_environments(self, n_envs: int = 1, use_subproc_vec_env=False) -> VecEnv:
        if self.env_type is None:
            raise ValueError("env_type must be set before creating the environment. It is currently None.")

        if n_envs > 1 and not use_subproc_vec_env:
            printc("WARNING! n_envs > 1 but use_subproc_vec_env is False. "
                   "Setting use_subproc_vec_env to True is recommended.", color="yellow")

        vec_env_cls = SubprocVecEnv if use_subproc_vec_env else None
        return make_vec_env(lambda: EnvManager(self.env_type).get_env(), n_envs=n_envs, vec_env_cls=vec_env_cls)

    def _load_model(self, path: str = None, env: VecEnv = None) -> PPO | MaskablePPO:
        path = path or self.final_model_path
        return self.model_cls.load(path, env)

    def _load_normalization_stats(self, path: str = None, env: VecEnv = None, for_training: bool = True) -> VecNormalize:
        if hasattr(self.training_config.normalizer, 'load'):
            path = path or self.norm_stats_path
            norm_env = self.training_config.normalizer.load(path, env)

            if not for_training:
                norm_env.training = False
                norm_env.norm_reward = False
        else:
            norm_env = env

        return norm_env
