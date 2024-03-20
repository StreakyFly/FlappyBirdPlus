from stable_baselines3 import PPO
from stable_baselines3.common.env_util import make_vec_env
from stable_baselines3.common.vec_env import VecNormalize
from stable_baselines3.common.callbacks import CheckpointCallback

from .env_manager import EnvManager


MODEL_NAME = 'flappy_bird'
DIR_MODELS = './ai-models'
DIR_CHECKPOINTS = f"{DIR_MODELS}/model_checkpoints"


def train(norm_env=None, model=None):
    if norm_env is None:
        env = create_environments(n_envs=5)

        # wrap the environment in a VecNormalize object
        norm_env = VecNormalize(env, norm_obs=True, norm_reward=True, clip_obs=10.0)

    if model is None:
        # create the model, using the normalized environment
        # use cpu, because it's faster than gpu in this case
        model = PPO('MlpPolicy', norm_env, verbose=1, tensorboard_log=f"{DIR_MODELS}/tensorboard_logs/", device='cpu',
                    learning_rate=0.0003, n_steps=2048, batch_size=64, gamma=0.99, clip_range=0.2)

    # save the model every 100.000 steps
    checkpoint_callback = CheckpointCallback(save_freq=100_000, save_path=DIR_CHECKPOINTS, name_prefix=MODEL_NAME)

    # train the model
    model.learn(total_timesteps=2_000_000, tb_log_name=MODEL_NAME, callback=checkpoint_callback)

    # save the model and the normalization statistics
    model.save(f"{DIR_CHECKPOINTS}/{MODEL_NAME}_2")
    norm_env.save(f"{DIR_CHECKPOINTS}/{MODEL_NAME}_normalization_stats_2.pkl")


def continue_training():
    env = create_environments(n_envs=5)
    norm_env = load_normalization_stats(path="./ai-models/model_checkpoints/flappy_bird_normalization_stats.pkl", env=env)
    model = load_model(path="./ai-models/model_checkpoints/flappy_bird_1000000_steps", env=norm_env)

    train(norm_env, model)


def run():
    env = create_environments()
    norm_env = load_normalization_stats(path=f"{DIR_CHECKPOINTS}/{MODEL_NAME}_normalization_stats_2.pkl", env=env)
    model = load_model(path=f"{DIR_CHECKPOINTS}/flappy_bird_3500000_steps-best", env=norm_env)

    # run the model
    obs = norm_env.reset()
    for _ in range(10000):
        action, _ = model.predict(obs, deterministic=True)
        obs, _, done, _ = norm_env.step(action)
        if done:
            obs = norm_env.reset()
    norm_env.close()


def evaluate() -> None:
    pass
    # env = create_environments(n_envs=6)
    # norm_env = load_normalization_stats(path=NORMALIZATION_STATS_PATH, env=env, for_training=False)
    # model = load_model(MODEL_PATH, env=norm_env)
    #
    # mean_reward, std_reward = evaluate_policy(model, model.get_env(), n_eval_episodes=10)
    # print(f"mean_reward: {mean_reward: .2f} +/- {std_reward: .2f}")


def create_environments(n_envs: int = 1):
    env = make_vec_env(lambda: EnvManager().get_env(), n_envs=n_envs)
    return env


def load_model(path: str = None, env=None):
    path = path or f"{DIR_CHECKPOINTS}/{MODEL_NAME}"
    model = PPO.load(path, env)
    return model


def load_normalization_stats(path: str = None, env=None):
    path = path or f"{DIR_CHECKPOINTS}/{MODEL_NAME}_normalization_stats.pkl"
    norm_env = VecNormalize.load(path, env)
    return norm_env
