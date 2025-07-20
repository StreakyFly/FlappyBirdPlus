from dataclasses import dataclass, field
from typing import Callable, Optional

from torch import nn

from src.ai.normalizers.vec_box_only_normalize import VecBoxOnlyNormalize

"""
This training config is currently used to set the hyperparameters for the PPO algorithm ONLY.
If you want to use a different algorithm, turn this into a BaseTrainingConfig class and
create a new class for each algorithm that inherits from it.
"""


@dataclass
class TrainingConfig:
    """
    Configuration for PPO training. Hyperparameters, model architecture, and normalization settings.
    """

    learning_rate: float = 0.0003  # learning rate for optimizer - controls how fast model updates
    n_steps: int = 2048  # steps per rollout before each policy update
    batch_size: int = 64  # number of samples per gradient step
    gamma: float = 0.99  # discount factor for future rewards
    gae_lambda: float = 0.95  # bias-variance tradeoff for advantage estimation (GAE)
    clip_range: float = 0.2  # range for clipping PPO policy updates
    ent_coef: float = 0.001  # coefficient for entropy bonus (encourages exploration)
    vf_coef: float = 0.5  # value function coefficient for the loss calculation

    policy_kwargs: dict = field(default_factory=lambda: dict(
        net_arch=dict(pi=[64, 64], vf=[64, 64]),  # policy/value network sizes
        activation_fn=nn.Tanh,  # activation function
        ortho_init=True,  # orthogonal weight initialization
    ))

    save_freq: int = 10_000  # steps between model saves
    total_timesteps: int = 1_000_000  # total training steps

    normalizer: Optional[Callable] = VecBoxOnlyNormalize  # observation/reward normalization wrapper
    clip_norm_obs: float = 10.0  # clip normalized obs to this range
    frame_stack: int = -1  # number of frames to stack together (-1 = none)
