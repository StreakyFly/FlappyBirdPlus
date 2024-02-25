from stable_baselines3 import PPO
from stable_baselines3.common.env_util import make_vec_env

from .flappy_bird_env import FlappyBirdEnv


# create the environment
env = make_vec_env(lambda: FlappyBirdEnv(), n_envs=1)

# create the model
model = PPO("MlpPolicy", env, verbose=1)

# train the model
model.learn(total_timesteps=100000)
