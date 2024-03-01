from stable_baselines3 import PPO
from stable_baselines3.common.env_util import make_vec_env
from stable_baselines3.common.vec_env import VecNormalize

from .flappy_bird_env import FlappyBirdEnv


def train():
    # create the environment(s)
    env = make_vec_env(lambda: FlappyBirdEnv(), n_envs=5)

    # wrap the environment in a VecNormalize object
    norm_env = VecNormalize(env, norm_obs=True, norm_reward=True, clip_obs=10.0)

    # create the model, using the normalized environment
    model = PPO("MlpPolicy", norm_env, verbose=1, n_steps=1024, batch_size=32)  # n_steps=2048, batch_size=64

    # train the model
    model.learn(total_timesteps=10000000)

    # save the model and the normalization statistics
    model.save("flappy_bird_model")
    norm_env.save("flappy_bird_normalization_stats.pkl")


def run():
    # create the environment
    env = make_vec_env(lambda: FlappyBirdEnv(), n_envs=1)

    # load the trained model
    model = PPO.load("flappy_bird_model")

    # load the normalization statistics
    env = VecNormalize.load("flappy_bird_normalization_stats.pkl", env)

    # run the model
    obs = env.reset()
    for _ in range(1000):
        action, _ = model.predict(obs, deterministic=True)
        obs, _, done, _ = env.step(action)
        if done:
            obs = env.reset()
    env.close()
