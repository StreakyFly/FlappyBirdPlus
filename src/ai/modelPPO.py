import json
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
from stable_baselines3.common.vec_env import VecEnv, SubprocVecEnv, VecEnvWrapper, VecFrameStack

from src.utils import printc
from .environments import EnvManager
from .environments.base_env import BaseEnv
from .training_config import TrainingConfig


# TODO Action masking hasn't been tested yet, so it's possible that it hasn't been implemented properly.
#  Some necessary adjustments might be missing, so if something isn't working properly, the issue is
#  probably somewhere in this file.
#  Docs: https://sb3-contrib.readthedocs.io/en/master/modules/ppo_mask.html


class ModelPPO:
    def __init__(self, env_type=None, env_variant=None, run_id=None) -> None:
        self.env_type = env_type
        self.env_variant = env_variant
        self.model_name = self.env_type.value
        self.run_id = run_id or f"run_{self._get_current_time()}"

        self.env_class: Type[BaseEnv] = EnvManager(self.env_type, self.env_variant).get_env_class()
        self.training_config: TrainingConfig = self.env_class.get_training_config()
        self.use_action_masking = getattr(self.env_class, 'requires_action_masking', False)
        self.model_cls = MaskablePPO if self.use_action_masking else PPO

        self.checkpoints_dir = None
        self.tensorboard_dir = None
        self.training_config_dir = None
        self.final_model_path = None
        self.norm_stats_path = None

        self._initialize_directories()

    @staticmethod
    def _get_current_time(time_format: str = '%Y%m%d_%H%M%S') -> str:
        return time.strftime(time_format)

    def _initialize_directories(self) -> None:
        base_dir = os.path.join('ai-models', 'PPO', self.env_type.value)
        run_dir = os.path.join(base_dir, self.run_id)
        self.checkpoints_dir = os.path.join(run_dir, 'checkpoints')
        self.tensorboard_dir = os.path.join(run_dir, 'tensorboard_logs')
        self.training_config_dir = os.path.join(run_dir, 'training_configs')
        self.final_model_path = os.path.join(run_dir, self.env_type.value)
        self.norm_stats_path = os.path.join(run_dir, self.env_type.value + '_normalization_stats.pkl')
        os.makedirs(run_dir, exist_ok=True)
        os.makedirs(self.checkpoints_dir, exist_ok=True)
        os.makedirs(self.tensorboard_dir, exist_ok=True)
        os.makedirs(self.training_config_dir, exist_ok=True)
        self._create_notes_file(dir_path=run_dir)

    def _save_training_config(self, continue_training: bool) -> None:
        import inspect

        def serialize(obj):
            if isinstance(obj, type):
                return f"{obj.__module__}.{obj.__name__}"
            return str(obj)

        # Add additional info to the training config
        config_dict = self.training_config.__dict__.copy()
        # Add policy_type
        config_dict['policy_type'] = self.model_cls.__name__
        # Add calculate_rewards() method's code
        config_dict['calculate_reward'] = inspect.getsource(self.env_class.calculate_reward)
        # Add entire environment file code and its inheritance tree until BaseEnv
        env_files = {}
        for cls in inspect.getmro(self.env_class):
            if cls == BaseEnv:
                break
            file_path = inspect.getfile(cls)
            if file_path not in env_files:
                with open(file_path, 'r') as f:
                    relative_path = os.path.relpath(file_path, start='')
                    env_files[relative_path] = f.read()
        config_dict['environment_files'] = env_files

        filename = f"training_config_{'initial_' if not continue_training else 'updated_'}{self._get_current_time()}.json"
        config_path = os.path.join(self.training_config_dir, filename)
        with open(config_path, 'w') as f:
            json.dump(config_dict, f, indent=4, default=serialize)

    def _create_notes_file(self, dir_path: str) -> None:
        notes_path = os.path.join(dir_path, 'notes.md')
        if not os.path.exists(notes_path):
            with open(notes_path, 'w') as f:
                f.write(f"# Training Notes\n")
                f.write(f"**Start Time**: {self._get_current_time(time_format='%d. %m. %Y %H:%M:%S')}\n\n")

    def train(self, norm_venv: VecEnvWrapper = None, model=None, continue_training: bool = False) -> None:
        self._save_training_config(continue_training=continue_training)

        if not continue_training:
            venv = self._create_venv(n_envs=6, use_subproc_vec_env=True)
            norm_venv = self._wrap_with_normalizer(path=self.norm_stats_path, venv=venv, load_existing=False)
            norm_venv = self._wrap_with_frame_stack(norm_venv)

        if model is None:
            policy = 'MultiInputPolicy' if isinstance(norm_venv.observation_space, spaces.Dict) else 'MlpPolicy'
            # create the model using the normalized environment; use cpu as it's faster than gpu in this case
            model = self.model_cls(
                policy, norm_venv, verbose=1, device='cpu', tensorboard_log=self.tensorboard_dir,
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
        norm_venv.save(self.norm_stats_path)

    def continue_training(self) -> None:
        venv = self._create_venv(n_envs=6, use_subproc_vec_env=True)
        norm_env = self._wrap_with_normalizer(path=self.norm_stats_path, venv=venv)
        norm_env = self._wrap_with_frame_stack(norm_env)
        model = self._load_model(path=self.final_model_path, venv=norm_env)

        self.train(norm_env, model, continue_training=True)

    def run(self) -> None:
        env = self._create_venv(n_envs=1, use_subproc_vec_env=False)
        norm_env = self._wrap_with_normalizer(path=self.norm_stats_path, venv=env, for_training=False)
        norm_env = self._wrap_with_frame_stack(norm_env)
        model = self._load_model(path=self.final_model_path, venv=norm_env)

        obs = norm_env.reset()
        while True:
            if self.use_action_masking:
                action_masks = norm_env.envs[0].env.action_masks()  # ಠ_ಠ
                action, _ = model.predict(obs, deterministic=True, action_masks=action_masks)
            else:
                action, _ = model.predict(obs, deterministic=True)
            obs, _, done, _ = norm_env.step(action)
            if done:
                obs = norm_env.reset()

    def evaluate(self) -> None:
        env = self._create_venv(n_envs=6, use_subproc_vec_env=True)
        norm_env = self._wrap_with_normalizer(path=self.norm_stats_path, venv=env, for_training=False)
        norm_env = self._wrap_with_frame_stack(norm_env)
        model = self._load_model(path=self.final_model_path, venv=norm_env)

        printc("WARNING! Each episode ends after termination. "
               "If termination never happens, the episode will never end.", color="yellow")

        evaluate_policy = maskable_evaluate_policy if self.use_action_masking else normal_evaluate_policy
        mean_reward, std_reward = evaluate_policy(model, model.get_env(), n_eval_episodes=10, deterministic=True, reward_threshold=None)
        print(f"mean_reward: {mean_reward: .2f} +/- {std_reward: .2f}")
        norm_env.close()

    def _create_venv(self, n_envs: int = 1, use_subproc_vec_env=False) -> VecEnv:
        """
        Creates a vectorized environment with the specified number of environments.
        """
        if self.env_type is None:
            raise ValueError("env_type must be set before creating the environment. It is currently None.")

        if n_envs > 1 and not use_subproc_vec_env:
            printc("WARNING! n_envs > 1 but use_subproc_vec_env is False. "
                   "Setting use_subproc_vec_env to True is recommended.", color="yellow")

        vec_env_cls = SubprocVecEnv if use_subproc_vec_env else None
        return make_vec_env(lambda: EnvManager(self.env_type, self.env_variant).get_env(), n_envs=n_envs, vec_env_cls=vec_env_cls)

    def _load_model(self, path: str = None, venv: VecEnv = None) -> PPO | MaskablePPO:
        path = path or self.final_model_path
        return self.model_cls.load(path, venv)

    def _wrap_with_normalizer(self, path: str = None, venv: VecEnv = None, for_training: bool = True, load_existing: bool = True) -> VecEnvWrapper:
        """
        Wraps the environment with a normalizer.
        If load_existing is True and the normalizer has a load method, it will load the normalization
        statistics from the specified path and wrap the environment with the loaded normalizer.
        Otherwise, it will wrap the environment with a new normalizer.
        """
        if self.training_config.normalizer is None:
            # The easiest fix would probably be to put "return VecEnvWrapper(venv)" here, but I haven't tested it yet.
            raise ValueError("Normalizer is set to None. If you are certain this is intentional, modify the code to proceed.")

        if load_existing and hasattr(self.training_config.normalizer, 'load'):
            path = path or self.norm_stats_path

            # This workaround is needed because VecBoxOnlyNormalize turns spaces.Discrete to spaces.Box for training,
            # so we must apply the same preprocessing when loading to avoid observation space mismatches.
            # Yes - we also wrap it with VecBoxOnlyNormalize when loading, but the sanity check that checks if
            # set observation space matches the saved observation space is ran before the wrapper is applied,
            # so it throws an error if we don't preprocess the observation space before wrapping it.
            if isinstance(venv.observation_space, spaces.Dict) and hasattr(self.training_config.normalizer, 'preprocess_observation_space'):
                new_space, _ = self.training_config.normalizer.preprocess_observation_space(venv.observation_space)
                venv.observation_space = new_space

            norm_env = self.training_config.normalizer.load(path, venv)

            if not for_training:
                norm_env.training = False
                norm_env.norm_reward = False
        else:
            norm_env = self.training_config.normalizer(venv, norm_obs=True, norm_reward=True, clip_obs=self.training_config.clip_norm_obs)

        return norm_env

    def _wrap_with_frame_stack(self, venv: VecEnv) -> VecEnvWrapper:
        """
        Wraps the environment with VecFrameStack if frame stacking is enabled.
        """
        if self.training_config.frame_stack > 1:
            return VecFrameStack(venv, n_stack=self.training_config.frame_stack)
        return venv if isinstance(venv, VecEnvWrapper) else VecEnvWrapper(venv)
