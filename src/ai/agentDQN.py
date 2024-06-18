from stable_baselines3 import DQN
from stable_baselines3.common.env_util import make_vec_env
from stable_baselines3.common.vec_env import VecNormalize, VecEnv
from stable_baselines3.common.callbacks import CheckpointCallback
from stable_baselines3.common.evaluation import evaluate_policy

from .env_manager import EnvManager


# Dumbass me learnt that DQN doesn't work with MultiDiscrete observation spaces after training and perfecting
# the (almost) only agent that doesn't need MultiDiscrete OS.

class AgentDQN:
    EXTRA_NAME = "7500000_steps"

    MODEL_NAME = 'flappy_bird'
    DIR_MODELS = './ai-models/DQN'
    DIR_CHECKPOINTS = f"{DIR_MODELS}/model_checkpoints"
    NORMALIZATION_STATS_END = "normalization_stats.pkl"
    MODEL_PATH = f"{DIR_CHECKPOINTS}/{MODEL_NAME}_{EXTRA_NAME}"
    # NORMALIZATION_STATS_PATH = f"{DIR_CHECKPOINTS}/{MODEL_NAME}_{EXTRA_NAME}_{NORMALIZATION_STATS_END}"
    NORMALIZATION_STATS_PATH = f"{DIR_CHECKPOINTS}/{MODEL_NAME}_vecnormalize_{EXTRA_NAME}.pkl"
    REPLAY_BUFFER_PATH = f"{DIR_CHECKPOINTS}/{MODEL_NAME}_replay_buffer_{EXTRA_NAME}.pkl"

    def __init__(self, env_type=None):
        self.env_type = env_type

    def train(self, norm_env=None, model=None, continue_training: bool = False) -> None:
        if norm_env is None:
            env = self.create_environments(n_envs=6)

            # wrap the environment in a VecNormalize object
            norm_env = VecNormalize(env, norm_obs=True, norm_reward=True, clip_obs=10.0)

        if model is None:
            # create the model, using the normalized environment
            # use cpu, because it's faster than gpu in this case
            model = DQN('MlpPolicy', norm_env, verbose=1, tensorboard_log=f"{self.DIR_MODELS}/tensorboard_logs/", device='cpu',
                        learning_rate=0.0002, buffer_size=2_000_000, batch_size=128, gamma=0.99, exploration_fraction=0.1,
                        exploration_final_eps=0.03, target_update_interval=10_000, learning_starts=30_000)

        reset_num_timesteps = True
        if continue_training:
            model._last_obs = None  # TODO not sure if this is necessary
            reset_num_timesteps = False

        # save the model, normalization statistics and the replay buffer every 100.000 steps
        checkpoint_callback = CheckpointCallback(save_freq=100_000, save_path=self.DIR_CHECKPOINTS, name_prefix=self.MODEL_NAME,
                                                 save_vecnormalize=True, save_replay_buffer=True)

        # train the model
        model.learn(total_timesteps=10_000_000, tb_log_name=self.MODEL_NAME,
                    callback=checkpoint_callback, reset_num_timesteps=reset_num_timesteps)

        # save the final model, the replay buffer & the normalization statistics
        model.save(self.MODEL_PATH)
        model.save_replay_buffer(self.REPLAY_BUFFER_PATH)
        norm_env.save(self.NORMALIZATION_STATS_PATH)

    def continue_training(self) -> None:
        env = self.create_environments(n_envs=6)
        norm_env = self.load_normalization_stats(path=self.NORMALIZATION_STATS_PATH, env=env)
        model = self.load_model(self.MODEL_PATH, env=norm_env, load_replay_buffer=True)

        self.train(norm_env, model, continue_training=True)

    def run(self) -> None:
        env = self.create_environments(n_envs=1)
        norm_env = self.load_normalization_stats(path=self.NORMALIZATION_STATS_PATH, env=env, for_training=False)
        model = self.load_model(self.MODEL_PATH, env=norm_env)

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
        norm_env = self.load_normalization_stats(path=self.NORMALIZATION_STATS_PATH, env=env, for_training=False)
        model = self.load_model(self.MODEL_PATH, env=norm_env)

        print("WARNING! Each episode ends after termination. If termination never happens, the episode will never end.")

        mean_reward, std_reward = evaluate_policy(model, model.get_env(), n_eval_episodes=10, deterministic=True, reward_threshold=None)
        print(f"mean_reward: {mean_reward: .2f} +/- {std_reward: .2f}")
        norm_env.close()

    def create_environments(self, n_envs: int = 1) -> VecEnv:
        if self.env_type is None:
            raise ValueError("env_type must be set before creating the environment")

        env = make_vec_env(lambda: EnvManager(self.env_type).get_env(), n_envs=n_envs)
        return env

    def load_model(self, path: str = None, env: VecEnv = None, load_replay_buffer: bool = False) -> DQN:
        path = path or f"{self.DIR_CHECKPOINTS}/{self.MODEL_NAME}"
        model = DQN.load(path, env)

        if load_replay_buffer:
            model.load_replay_buffer(self.REPLAY_BUFFER_PATH)

        return model

    def load_normalization_stats(self, path: str = None, env: VecEnv = None, for_training: bool = True) -> VecNormalize:
        path = path or f"{self.DIR_CHECKPOINTS}/{self.MODEL_NAME}_{self.NORMALIZATION_STATS_END}"
        norm_env = VecNormalize.load(path, env)

        if not for_training:
            norm_env.training = False
            norm_env.norm_reward = False

        return norm_env
