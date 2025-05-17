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
    # learning rate for the optimizer - controls how quickly the model updates its parameters
    learning_rate: float = 0.0003
    # number of environment steps to run before each policy update
    n_steps: int = 2048
    # number of samples used per gradient update
    batch_size: int = 64
    # discount factor for future rewards - closer to 1 means longer-term memory
    gamma: float = 0.99
    # range for clipping policy updates to stabilize training
    clip_range: float = 0.2

    # policy architecture and settings
    policy_kwargs: dict = field(default_factory=lambda: dict(
        # hidden layer sizes for the policy network (pi) and value function network (vf)
        net_arch = dict(pi=[64, 64], vf=[64, 64]),
        # activation function used between layers
        activation_fn = nn.Tanh,
        # whether to use orthogonal initialization for weights (helps with stability)
        ortho_init = True,
    ))

    # how often to save the model
    save_freq: int = 10_000
    # total number of environment steps to train for
    total_timesteps: int = 1_000_000

    # optional wrapper to normalize observations and/or rewards
    normalizer: Optional[Callable] = VecBoxOnlyNormalize
    # max abs value for normalized observations
    clip_norm_obs: float = 10.0
