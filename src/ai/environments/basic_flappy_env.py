import numpy as np
import gymnasium as gym

import pygame

from .base_env import BaseEnv
from .basic_flappy_state import get_state


class BasicFlappyEnv(BaseEnv):
    def __init__(self):
        super().__init__()

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
            low=np.array([-120, -17, 0, -650, -650], dtype=np.float32),
            high=np.array([755, 21, 500, 550, 550], dtype=np.float32),
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
        if action == 1:
            self.player.flap()

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

        pygame.display.update()
        self.config.tick()

        return (self.get_state(),
                self.calculate_reward(action=action, died=terminated, passed_pipe=passed_pipe),
                terminated,
                False,
                {})

    def get_state(self):
        return get_state(self.player, self.pipes, self.get_pipe_pair_center)

    def calculate_reward(self, action, died, passed_pipe) -> int:
        reward = 0
        if died:
            reward -= 1000
        else:
            reward += 1
        if passed_pipe:
            reward += 100
        if action == 1:
            reward -= 0.2

        for i, pipe in enumerate(self.pipes.upper):
            if pipe.x + pipe.w < self.player.x:
                continue
            else:
                pipe_center_y = self.get_pipe_pair_center((pipe, self.pipes.lower[i]))[1]
                vertical_distance_to_pipe_pair_center = abs(self.player.cy - pipe_center_y)
                # pygame.draw.circle(self.config.screen, (255, 0, 0), (pipe.cx, pipe_center_y), 5)
                # pygame.draw.line(self.config.screen, (255, 0, 0), (self.player.cx, self.player.cy), (pipe.cx, pipe_center_y), 2)
                if vertical_distance_to_pipe_pair_center < 150:
                    reward += 3  # 4
                break

        return reward
