import gymnasium as gym
import numpy as np
from stable_baselines3.common.vec_env import VecEnvWrapper

"""
###############################################
###        WARNING! DO NOT USE THIS!        ###
### Unless you want bad results... (｡◕‿‿◕｡) ###
###############################################

This was quickly thrown together with ChatGPT's help — it hasn't been thought through, nor properly tested.
It might normalize observations incorrectly, fail in subtle ways, or just not work at all. It doesn't even normalize rewards.
Therefore, do NOT rely on this until you do extensive testing and compare it to the official VecNormalize class.

Then why did I even write it (well... copy-pasted it from ChatGPT)? I wanted to experiment with custom normalizers a
bit — specifically to try [0, 1] scaling instead of the [-1, 1] range you typically get with VecNormalize. While [0, 1]
might seem more ReLU-friendly, in practice VecNormalize works just fine with ReLU in most cases and is way more reliable.

This class uses static observation_space.low/high values for normalization, which can be wildly off from the actual
data distribution. That can easily lead to completely broken training. A proper MinMax implementation would require
tracking running min and max — which I didn’t bother with (yet?).

Another thing you could do instead of this is simply shift the output of VecNormalize to the [0, 1] range.
"""


class VecMinMaxNormalize(VecEnvWrapper):
    """
    VecEnvWrapper that normalizes observations from Box or Dict[Box] spaces to [0, 1],
    based on observation_space.low and observation_space.high.
    """

    def __init__(self, venv, **kwargs):
        super().__init__(venv)

        if isinstance(venv.observation_space, gym.spaces.Box):
            self.low = venv.observation_space.low
            self.high = venv.observation_space.high
            self.obs_is_dict = False

        elif isinstance(venv.observation_space, gym.spaces.Dict):
            self.low = {
                key: space.low for key, space in venv.observation_space.spaces.items()
                if isinstance(space, gym.spaces.Box)
            }
            self.high = {
                key: space.high for key, space in venv.observation_space.spaces.items()
                if isinstance(space, gym.spaces.Box)
            }
            self.obs_is_dict = True

        else:
            raise NotImplementedError("Only Box and Dict[Box] observation spaces are supported.")

    def reset(self):
        obs = self.venv.reset()
        return self._normalize(obs)

    def step_wait(self):
        obs, rewards, dones, infos = self.venv.step_wait()
        return self._normalize(obs), rewards, dones, infos

    def _normalize(self, obs):
        def normalize_array(x, low, high):
            return np.clip((x - low) / (high - low + 1e-8), 0.0, 1.0)

        if self.obs_is_dict:
            return {
                key: normalize_array(obs[key], self.low[key], self.high[key])
                if key in self.low else obs[key]
                for key in obs
            }
        else:
            return normalize_array(obs, self.low, self.high)
