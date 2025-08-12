import json
import os
import time
from typing import Type, Union

import numpy as np
from gymnasium import spaces
from sb3_contrib import MaskablePPO
# from sb3_contrib.common.maskable.callbacks import MaskableEvalCallback
from sb3_contrib.common.maskable.evaluation import evaluate_policy as maskable_evaluate_policy
from stable_baselines3 import PPO
from stable_baselines3.common.callbacks import BaseCallback, CallbackList
from stable_baselines3.common.callbacks import CheckpointCallback
from stable_baselines3.common.env_util import make_vec_env
from stable_baselines3.common.evaluation import evaluate_policy as normal_evaluate_policy
from stable_baselines3.common.vec_env import VecEnv, SubprocVecEnv, VecEnvWrapper, VecFrameStack

from src.config import Config
from src.utils import printc, set_random_seed
from .environments import EnvManager, EnvType
from .environments.base_env import BaseEnv
from .environments.env_types import EnvVariant
from .training_config import TrainingConfig


class ModelPPO:
    def __init__(self, env_type=None, env_variant=None, run_id=None) -> None:
        self.env_type: EnvType = env_type
        self.env_variant: EnvVariant = env_variant
        self.model_name: str = self.env_type.value
        self.run_id: str = run_id or f"run_{self._get_current_time()}"

        self.env_class: Type[BaseEnv] = EnvManager(self.env_type, self.env_variant).get_env_class()
        self.training_config: TrainingConfig = self.env_class.get_training_config()
        self.use_action_masking: bool = getattr(self.env_class, 'REQUIRES_ACTION_MASKING', False)
        self.model_cls: Type[Union[PPO, MaskablePPO]] = MaskablePPO if self.use_action_masking else PPO

        self.seed: int = Config.seed  # seed for the training (applied globally(?), so it affects the model and all environments)
        self.num_cores: int = Config.num_cores  # number of cores to use during training

        # Prepare paths for various directories and files
        base_dir = os.path.join('ai-models', 'PPO', self.env_type.value)
        self.run_dir = os.path.join(base_dir, self.run_id)
        self.checkpoints_dir = os.path.join(self.run_dir, 'checkpoints')
        self.tensorboard_dir = os.path.join(self.run_dir, 'tensorboard_logs')
        self.monitor_dir = os.path.join(self.run_dir, 'monitor_logs', f"session_{self._get_current_time()}")
        self.training_config_dir = os.path.join(self.run_dir, 'training_configs')
        self.final_model_path = os.path.join(self.run_dir, self.env_type.value)
        self.norm_stats_path = os.path.join(self.run_dir, self.env_type.value + '_normalization_stats.pkl')

    def train(self, norm_venv: VecEnvWrapper = None, model=None, continue_training: bool = False) -> None:
        self._initialize_directories()
        self._save_training_config(continue_training=continue_training)

        if not continue_training:
            venv = self._create_venv(n_envs=self.num_cores, use_subproc_vec_env=True, monitor=True)
            norm_venv = self._wrap_with_normalizer(path=self.norm_stats_path, venv=venv, load_existing=False)
            norm_venv = self._wrap_with_frame_stack(norm_venv)

        if model is None:
            policy = 'MultiInputPolicy' if isinstance(norm_venv.observation_space, spaces.Dict) else 'MlpPolicy'
            # create the model using the normalized environment
            # use cpu as it's faster than gpu in most cases with PPO:
            #  https://stable-baselines3.readthedocs.io/en/master/modules/ppo.html
            model = self.model_cls(
                policy, norm_venv, verbose=1, device='cpu', seed=self.seed, tensorboard_log=self.tensorboard_dir,
                learning_rate=self.training_config.learning_rate,
                n_steps=self.training_config.n_steps,
                batch_size=self.training_config.batch_size,
                gamma=self.training_config.gamma,
                gae_lambda=self.training_config.gae_lambda,
                clip_range=self.training_config.clip_range,
                ent_coef=self.training_config.ent_coef,
                vf_coef=self.training_config.vf_coef,
                policy_kwargs=self.training_config.policy_kwargs,
            )

        if continue_training:
            model._last_obs = None  # TODO Is this necessary? If not, remove it.
            model.tensorboard_log = self.tensorboard_dir
            # TODO: I DON'T THINK YOU CAN ACTUALLY CHANGE THESE, JUST LIKE THAT, WHEN CONTINUING TRAINING?
            #  Idk, gotta try 👍
            # Update certain model parameters from the training config
            # model.learning_rate = self.training_config.learning_rate
            # model.n_steps = self.training_config.n_steps
            # model.batch_size = self.training_config.batch_size
            # model.gamma = self.training_config.gamma
            # model.gae_lambda = self.training_config.gae_lambda
            # model.clip_range = self.training_config.clip_range

        # save the model & normalization statistics every N steps
        checkpoint_callback = CheckpointCallback(
            save_freq=self.training_config.save_freq,  # this number is basically multiplied by n_envs
            save_path=self.checkpoints_dir,
            name_prefix=self.model_name,
            save_vecnormalize=True)

        callback_list = CallbackList([checkpoint_callback, LogAllInfoCallback()])

        # train the model
        model.learn(
            total_timesteps=self.training_config.total_timesteps,
            tb_log_name=self.model_name,
            callback=callback_list,
            reset_num_timesteps=not continue_training)

        # save the final model & the normalization statistics
        model.save(self.final_model_path)
        norm_venv.save(self.norm_stats_path)

    def continue_training(self) -> None:
        self._ensure_run_dir_exist()
        venv = self._create_venv(n_envs=self.num_cores, use_subproc_vec_env=True, monitor=True)
        norm_env = self._wrap_with_normalizer(path=self.norm_stats_path, venv=venv)
        norm_env = self._wrap_with_frame_stack(norm_env)
        model = self._load_model(path=self.final_model_path, venv=norm_env)

        self.train(norm_env, model, continue_training=True)

    def run(self) -> None:
        self._ensure_run_dir_exist()
        self._load_training_config()
        env = self._create_venv(n_envs=1, use_subproc_vec_env=False, monitor=False)
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
        self._ensure_run_dir_exist()
        self._load_training_config()
        env = self._create_venv(n_envs=self.num_cores, use_subproc_vec_env=True, monitor=False)
        norm_env = self._wrap_with_normalizer(path=self.norm_stats_path, venv=env, for_training=False)
        norm_env = self._wrap_with_frame_stack(norm_env)
        model = self._load_model(path=self.final_model_path, venv=norm_env)
        # Print model's policy weights
        # for name, param in model.policy.named_parameters():
        #     print(f"Layer: {name}, Weights: {param.data}")

        printc("[INFO] Evaluating the model...", color="blue")
        printc("[WARN] Each episode ends after termination. If termination never happens, the episode will never end.", color="yellow")

        N_EVAL_EPISODES = 50
        evaluate_policy = maskable_evaluate_policy if self.use_action_masking else normal_evaluate_policy
        episode_rewards, episode_lengths = evaluate_policy(
            model, model.get_env(), n_eval_episodes=N_EVAL_EPISODES, deterministic=True, reward_threshold=None, return_episode_rewards=True
        )
        print(f"episodes={N_EVAL_EPISODES}")
        print("episode lengths:", episode_lengths)
        print("episode rewards:", [round(r, 2) for r in episode_rewards])
        mean_length = np.mean(episode_lengths)
        std_length = np.std(episode_lengths)
        mean_reward = np.mean(episode_rewards)
        std_reward = np.std(episode_rewards)
        print(f"mean_length: {mean_length:.2f} +/- {std_length:.2f}")
        print(f"mean_reward: {mean_reward:.2f} +/- {std_reward:.2f}")
        norm_env.close()

        results_path = os.path.join(self.run_dir, 'evaluation_results.txt')
        with open(results_path, 'a') as f:
            f.write(f"Evaluation at {self._get_current_time(time_format='%d.%m.%Y - %H:%M:%S')}:\n")
            f.write(f"episodes: {N_EVAL_EPISODES}\n")
            f.write(f"mean_length: {mean_length:.2f} +/- {std_length:.2f} {episode_lengths}\n")
            f.write(f"mean_reward: {mean_reward:.2f} +/- {std_reward:.2f} {[round(r, 2) for r in episode_rewards]}\n\n\n")

    def _create_venv(self, n_envs: int = 1, use_subproc_vec_env: bool = False, monitor: bool = False) -> VecEnv:
        """
        Creates a vectorized environment with the specified number of environments.
        """
        if self.env_type is None:
            raise ValueError("env_type must be set before creating the environment. It is currently None.")

        if n_envs > 1 and not use_subproc_vec_env:
            printc("[WARN] n_envs > 1 but use_subproc_vec_env is False. "
                   "Setting use_subproc_vec_env to True is recommended.", color="yellow")

        return make_vec_env(
            lambda: EnvManager(self.env_type, self.env_variant).get_env(),
            n_envs=n_envs,
            # seed=self.seed,  # just found out you can pass seed here, but I'm not gonna do it just yet, cuz my current seed logic "works"-ish and I don't wanna break it
            vec_env_cls=SubprocVecEnv if use_subproc_vec_env else None,
            monitor_dir=self.monitor_dir if monitor else None,
        )

    def _load_model(self, path: str = None, venv: VecEnv = None) -> PPO | MaskablePPO:
        path = path or self.final_model_path
        model = self.model_cls.load(path, venv)

        if Config.handle_seed:
            set_random_seed(Config.seed)  # set random seed after loading the model, to override the model's seed

        return model

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

    @staticmethod
    def _get_current_time(time_format: str = '%Y%m%d_%H%M%S') -> str:
        return time.strftime(time_format)

    def _initialize_directories(self) -> None:
        os.makedirs(self.run_dir, exist_ok=True)
        os.makedirs(self.checkpoints_dir, exist_ok=True)
        os.makedirs(self.tensorboard_dir, exist_ok=True)
        # os.makedirs(self.monitor_dir, exist_ok=True)  # Nuh-uh, don't create this dir yourself, it will be created when needed
        os.makedirs(self.training_config_dir, exist_ok=True)
        self._create_notes_file(dir_path=self.run_dir)

    def _ensure_run_dir_exist(self) -> None:
        """
        Ensures that the run directory exists. If it doesn't, it prints an error message and exits.
        """
        if not os.path.exists(self.run_dir):
            printc(f"[ERROR] Run directory '{self.run_dir}' does not exist. "
                   f"You either messed up the `run_id` or set the wrong mode. Exiting...", color="red", styles=['reverse'])
            raise FileNotFoundError(f"Run directory '{self.run_dir}' does not exist.")

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
        # Add seed used for training
        config_dict['seed'] = self.seed
        # Add calculate_rewards() method's code
        config_dict['calculate_reward'] = inspect.getsource(self.env_class.calculate_reward)
        # Add entire environment file code and its inheritance tree until BaseEnv
        env_files = {}
        for cls in inspect.getmro(self.env_class):
            if cls == BaseEnv:
                break
            file_path = inspect.getfile(cls)
            if file_path not in env_files:
                with open(file_path, 'r', encoding='utf-8') as f:
                    relative_path = os.path.relpath(file_path, start='')
                    env_files[relative_path] = f.read()
        config_dict['environment_files'] = env_files

        filename = f"training_config_{'initial_' if not continue_training else 'updated_'}{self._get_current_time()}.json"
        config_path = os.path.join(self.training_config_dir, filename)
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config_dict, f, indent=4, default=serialize)

    def _load_training_config(self) -> None:
        """
        Loads the training configuration from a JSON file and updates the currently used training_config.
        Why do we even need this?
        Currently, just for frame_stack afaik, because that must match what was used during training.
        But it loads more than just frame_stack, because why not.
        """
        # Get the oldest training config file
        config_files = sorted(
            [os.path.join(self.training_config_dir, f) for f in os.listdir(self.training_config_dir) if
             f.startswith("training_config_") and f.endswith(".json")],
            key=os.path.getctime
        )
        config_path = config_files[0] if config_files else None
        if config_path is None or not os.path.exists(config_path):
            printc(f"[WARN] Training config file not found: {config_path}. Using default training config.", color="orange")
            return

        if len(config_files) > 1:
            printc(
                f"[WARN] Multiple training config files found in {self.training_config_dir}. "
                f"Using the oldest (probably initial) one: {config_path}, because I am too lazy to come up "
                f"with logic that would choose the right one.", color="orange"
            )

        with open(config_path, 'r') as f:
            config_data = json.load(f)

        printc(f"[INFO] Loading training config from ...\\{"\\".join(config_path.split('\\')[-3:])}", color="green")

        # Update the training_config with the loaded data
        for key, value in config_data.items():
            if hasattr(self.training_config, key):
                if key in ['normalizer']:
                    printc(f"[WARN] Skipping attribute '{key}' as it is serialized and I am too lazy to de-serialize it.", color="yellow")
                else:
                    setattr(self.training_config, key, value)
            else:
                if key in ['policy_type', 'calculate_reward', 'environment_files']:
                    printc(f"[INFO] Skipping attribute '{key}' as it is not part of TrainingConfig.", color="blue")
                elif key in ['seed']:  # SB3 loads the seed from the trained model, so we don't need to set it here
                    printc(f"[INFO] Skipping attribute '{key}' as it should be handled elsewhere.", color="blue")
                else:
                    printc(f"[WARN] Unexpected attribute '{key}' found in training config.", color="yellow")

        printc("[INFO] Training config loaded (well... at least partially).\n", color="green")

    def _create_notes_file(self, dir_path: str) -> None:
        notes_path = os.path.join(dir_path, 'notes.md')
        if not os.path.exists(notes_path):
            with open(notes_path, 'w') as f:
                f.write(f"# Training Notes\n")
                f.write(f"**Start Time**: {self._get_current_time(time_format='%d.%m.%Y %H:%M:%S')}\n\n")


class LogAllInfoCallback(BaseCallback):
    def __init__(self, prefix: str = "rollout_extra", verbose: int = 0):
        super().__init__(verbose)
        self.prefix = prefix
        self.episode_data = {}

    def _on_step(self) -> bool:
        for info, done in zip(self.locals["infos"], self.locals["dones"]):
            if done:  # ONLY log info at the end of each episode
                for key, value in info.items():
                    if key == "TimeLimit.truncated":  # exclude this key
                        continue
                    # If the value is a number, log it
                    elif isinstance(value, (int, float)):
                        if key not in self.episode_data:
                            self.episode_data[key] = []
                        self.episode_data[key].append(value)
        return True

    def _on_rollout_end(self) -> None:
        # Log the mean of collected values at the end of each rollout
        for key, values in self.episode_data.items():
            if values:
                mean_value = np.mean(values)
                self.logger.record(f"{self.prefix}/ep_{key}_mean", mean_value)
        # Clear buffer for the next rollout
        self.episode_data.clear()
