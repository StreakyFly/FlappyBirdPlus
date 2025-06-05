import gymnasium as gym
import numpy as np
import pygame
from torch import nn

from .base_env import BaseEnv
from ..controllers import BasicFlappyModelController
from ..normalizers.vec_box_only_normalize import VecBoxOnlyNormalize
from ..observations import ObservationManager
from ..training_config import TrainingConfig


class BasicFlappyEnv(BaseEnv):
    def __init__(self):
        self.observation_manager = ObservationManager()
        super().__init__()
        self.reset_env()

    def reset_env(self):
        super().reset_env()
        self.observation_manager.create_observation_instance(self.player, self)

    @staticmethod
    def get_training_config() -> TrainingConfig:
        VERSION: str = "default"  # which training config to use

        match VERSION:  # noqa
            case "default":
                training_config = TrainingConfig(
                    learning_rate=0.0003,
                    n_steps=2048,
                    batch_size=64,
                    gamma=0.99,
                    clip_range=0.2,
                    ent_coef=0.001,

                    policy_kwargs=dict(
                        # Out of [128, 128], [64, 64], [32, 32], [8, 8], [8], [4] and [2], the [16, 16] reached great results the fastest.
                        # It wasn't properly tested, only a single run was done with each of them,
                        # but all of them did amazing, with only some time difference.
                        # [8], [4] and [2] needed more total_timesteps to reach the same skill, but they were still able
                        # to reach it without any problems. [128, 128] took even longer (2x longer than [2] or 4x longer than [16, 16]).
                        # [1] however didn't learn, even after 6.5m timesteps (roughly 10x times what others needed for
                        # great results), maybe if I left it for longer it would have, but that's a problem for another day.
                        # So it seems like [16, 16] is the golden middle, going in either direction (lower or higher)
                        # makes the training slower with each neuron added/removed, but it still works until a certain point.
                        net_arch=dict(pi=[16, 16], vf=[16, 16]),
                        # The minimum network size that learned to play in reasonable time - just 2 neurons!
                        # net_arch=dict(pi=[2], vf=[2]),
                        activation_fn=nn.Tanh,
                        ortho_init=True,
                    ),

                    save_freq=40_000,
                    total_timesteps=800_000,

                    normalizer=VecBoxOnlyNormalize,
                    clip_norm_obs=10.0,
                )

            case "relu":
                training_config = TrainingConfig(
                    learning_rate=0.0003,
                    n_steps=2048,
                    batch_size=64,
                    gamma=0.99,
                    clip_range=0.1,  # smaller clip_range prevents policy collapse
                    ent_coef=0.001,

                    policy_kwargs=dict(
                        net_arch=dict(pi=[32, 32], vf=[32, 32]),
                        # ReLU variations: LeakyReLU (slower than ReLU but more stable), GELU (untested), ELU (untested)
                        activation_fn=nn.LeakyReLU,
                        ortho_init=True,
                    ),

                    save_freq=50_000,
                    total_timesteps=2_000_000,

                    normalizer=VecBoxOnlyNormalize,
                    # normalizer=VecMinMaxNormalize,  # the biggest garbage ever written, don't use if you value your time
                    clip_norm_obs=5.0,  #  smaller clip_norm_obs prevents policy collapse
                )

            case _:
                raise ValueError(f"Unknown training config version: {VERSION}")

        return training_config

    @staticmethod
    def get_action_and_observation_space():
        # 0: do nothing, 1: flap the wings
        action_space = gym.spaces.Discrete(2)

        # index 0 -> player y position
        # index 1 -> player y velocity
        # index 2 -> horizontal distance from player to the next pipe's right-most point
        # index 3 -> vertical distance from player to the next pipe's vertical center
        # index 4 -> vertical distance from player to the second next pipe's vertical center
        observation_space = gym.spaces.Box(
            low=np.array([-90, -17, 0, -650, -650], dtype=np.float32),
            high=np.array([785, 21, 500, 550, 550], dtype=np.float32),
            dtype=np.float32
        )

        return action_space, observation_space

    @staticmethod
    def get_observation_space_clip_modes() -> dict[str, int]:
        observation_space_clip_modes = {
            'box': 1
        }
        return observation_space_clip_modes

    def perform_step(self, action):
        BasicFlappyModelController.perform_action(self.player, action)

        terminated = False
        passed_pipe = False
        if self.player.crossed(self.next_closest_pipe_pair[0]):
            passed_pipe = True
            self.score.add()
            self.next_closest_pipe_pair = self.get_next_pipe_pair()

        self.player.handle_bad_collisions(self.pipes, self.floor)
        if self.is_player_dead():
            terminated = True

        for event in pygame.event.get():
            self.handle_quit(event)

        self.background.tick()
        self.pipes.tick()
        self.floor.tick()
        self.player.tick()
        self.score.tick()

        # Call calculate_reward before updating the display, if you want to visualize the pipe centers
        # (must uncomment the pygame.draw.circle and pygame.draw.line lines in calculate_reward)
        # self.calculate_reward(action=action, passed_pipe=passed_pipe)

        pygame.display.update()
        self.config.tick()

        return (self.get_observation(),
                self.calculate_reward(action=action, passed_pipe=passed_pipe),
                terminated,
                False,
                {})

    def get_observation(self):
        return self.observation_manager.get_observation(self.player)

    def calculate_reward(self, action, passed_pipe) -> float:
        reward = 0

        # lil punishment for flapping
        if action == 1:
            reward -= 0.1
        # big reward for passing a pipe
        if passed_pipe:
            reward += 5

        # lil reward for staying close to the center of the next pipe pair center
        for i, pipe in enumerate(self.pipes.upper):
            if pipe.x + pipe.w < self.player.x:
                continue
            else:
                pipe_center_y = self.get_pipe_pair_center((pipe, self.pipes.lower[i]))[1]
                vertical_distance_to_pipe_pair_center = abs(self.player.cy - pipe_center_y)
                # pygame.draw.circle(self.config.screen, (255, 0, 0), (pipe.cx, pipe_center_y), 5)
                # pygame.draw.line(self.config.screen, (255, 0, 0), (self.player.cx, self.player.cy), (pipe.cx, pipe_center_y), 2)
                if vertical_distance_to_pipe_pair_center < 200:
                    # up to 0.1 reward for being close to the center of the pipe pair
                    reward += 0.1 * (1 - vertical_distance_to_pipe_pair_center / 200)
                break

        return reward
