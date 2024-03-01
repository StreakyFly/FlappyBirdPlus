import gymnasium as gym
import numpy as np

from ..flappybird import FlappyBird
from ..utils import printc


class FlappyBirdEnv(gym.Env):
    metadata = {'render.modes': ['none', 'human']}  # this probably won't be used

    def __init__(self):
        super(FlappyBirdEnv, self).__init__()

        self.game = FlappyBird()
        self.game.init_env()

        self.action_space = gym.spaces.Discrete(2)  # 0: do nothing, 1: flap the wings
        # self.action_space = gym.spaces.MultiDiscrete([2, 3])  # for multiple actions

        self.observation_space = gym.spaces.Box(
            low=np.array([-120, -90, -265, 200, 125, 200, 515, 200, 905, 200], dtype=np.float32),
            high=np.array([755, 20, 300, 600, 510, 600, 900, 600, 1290, 600], dtype=np.float32),
            dtype=np.float32
        )

    def step(self, action):
        observation, reward, terminated, truncated = self.game.step(action)
        info = {}  # populate with additional info if necessary

        observation = np.clip(observation, self.observation_space.low, self.observation_space.high)

        return observation, reward, terminated, truncated, info

    def reset(self, *, seed: int | None = None, options: dict | None = None) -> tuple[np.ndarray, dict]:
        if seed or options:
            printc("WARNING: Seed and options are not supported yet in FlappyBird().", color='yellow')

        self.game.reset_env()

        # game_state = np.array([50, 0, 100, 300, 100, 200], dtype=np.float32)
        game_state = self.game.get_state()
        info = {}

        return game_state, info

    def render(self):
        # rendering is handled by the game itself
        pass

    def close(self):
        # this method isn't needed (yet)
        pass


def test_flappy_bird_env():
    env = FlappyBirdEnv()

    while True:
        action = env.action_space.sample()  # take a random action
        obs, reward, terminated, truncated, info = env.step(action)

        if terminated or truncated:
            env.reset()
