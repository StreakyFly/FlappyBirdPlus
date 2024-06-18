import os
import time

from stable_baselines3 import PPO
from stable_baselines3.common.env_util import make_vec_env
from stable_baselines3.common.vec_env import VecNormalize, VecEnv
from stable_baselines3.common.callbacks import CheckpointCallback
from stable_baselines3.common.evaluation import evaluate_policy

from .env_manager import EnvManager


class AgentPPO:

    def __init__(self, env_type=None, run_id=None) -> None:
        self.env_type = env_type
        self.model_name = self.env_type.value
        self.base_dir = os.path.join(r'.\ai-models', 'PPO', self.env_type.value)
        self.run_id = run_id if run_id else self._generate_run_id()

        self.tensorboard_dir = None
        self.run_dir = None
        self.checkpoints_dir = None
        self.final_model_path = None
        self.norm_stats_path = None

        self.initialize_directories()

    @staticmethod
    def _generate_run_id():
        return f"run_{time.strftime('%Y%m%d_%H%M%S')}"

    def initialize_directories(self) -> None:
        self.run_dir = os.path.join(self.base_dir, self.run_id)
        self.checkpoints_dir = os.path.join(self.run_dir, 'checkpoints')
        self.tensorboard_dir = os.path.join(self.run_dir, 'tensorboard_logs')
        self.final_model_path = os.path.join(self.run_dir, self.env_type.value)
        self.norm_stats_path = os.path.join(self.run_dir, self.env_type.value + '_normalization_stats.pkl')
        os.makedirs(self.run_dir, exist_ok=True)
        os.makedirs(self.checkpoints_dir, exist_ok=True)
        os.makedirs(self.tensorboard_dir, exist_ok=True)

    def train(self, norm_env=None, model=None, continue_training: bool = False) -> None:
        if norm_env is None:
            env = self.create_environments(n_envs=6)
            # wrap the environment in a VecNormalize object
            norm_env = VecNormalize(env, norm_obs=True, norm_reward=True, clip_obs=10.0)

        if model is None:
            # create the model, using the normalized environment
            # use cpu, because it's faster than gpu in this case
            model = PPO('MlpPolicy', norm_env, verbose=1, device='cpu',
                        tensorboard_log=self.tensorboard_dir,
                        learning_rate=0.0002,
                        n_steps=2048,
                        batch_size=64,
                        gamma=0.99,
                        clip_range=0.2)

        if continue_training:
            model._last_obs = None  # TODO Is this necessary? If not, remove it.

        # save the model & normalization statistics every 100.000 steps
        checkpoint_callback = CheckpointCallback(
            save_freq=25_000,  # this number is basically multiplied by n_envs
            save_path=self.checkpoints_dir,
            name_prefix=self.model_name,
            save_vecnormalize=True)

        # train the model
        model.learn(
            total_timesteps=10_000_000,
            tb_log_name=self.model_name,
            callback=checkpoint_callback,
            reset_num_timesteps=not continue_training)

        # save the final model & the normalization statistics
        model.save(self.final_model_path)
        norm_env.save(self.norm_stats_path)

    def continue_training(self) -> None:
        env = self.create_environments(n_envs=6)
        norm_env = self.load_normalization_stats(path=self.norm_stats_path, env=env)
        model = self.load_model(self.final_model_path, env=norm_env)

        self.train(norm_env, model, continue_training=True)

    def run(self) -> None:
        env = self.create_environments(n_envs=1)
        norm_env = self.load_normalization_stats(path=self.norm_stats_path, env=env, for_training=False)
        model = self.load_model(self.final_model_path, env=norm_env)

        obs = norm_env.reset()
        # for _ in range(10_000):
        while True:
            action, _ = model.predict(obs, deterministic=True)
            obs, _, done, _ = norm_env.step(action)
            if done:
                obs = norm_env.reset()
        # norm_env.close()

    def evaluate(self) -> None:
        env = self.create_environments(n_envs=6)
        norm_env = self.load_normalization_stats(path=self.norm_stats_path, env=env, for_training=False)
        model = self.load_model(self.final_model_path, env=norm_env)

        print("WARNING! Each episode ends after termination. If termination never happens, the episode will never end.")

        mean_reward, std_reward = evaluate_policy(model, model.get_env(), n_eval_episodes=10, deterministic=True, reward_threshold=None)
        print(f"mean_reward: {mean_reward: .2f} +/- {std_reward: .2f}")
        norm_env.close()

    def create_environments(self, n_envs: int = 1) -> VecEnv:
        if self.env_type is None:
            raise ValueError("env_type must be set before creating the environment. It is currently None.")
        return make_vec_env(lambda: EnvManager(self.env_type).get_env(), n_envs=n_envs)

    def load_model(self, path: str = None, env: VecEnv = None) -> PPO:
        path = path or self.final_model_path
        return PPO.load(path, env)

    def load_normalization_stats(self, path: str = None, env: VecEnv = None, for_training: bool = True) -> VecNormalize:
        path = path or self.norm_stats_path
        norm_env = VecNormalize.load(path, env)

        if not for_training:
            norm_env.training = False
            norm_env.norm_reward = False

        return norm_env
