import sys
import gymnasium as gym
import numpy as np

import pygame
from pygame import QUIT

from .base_env import BaseEnv


class BasicFlappyEnv(BaseEnv):
    def __init__(self):
        super().__init__()

    def get_action_and_observation_space(self):
        # self.action_space = gym.spaces.MultiDiscrete([2, 3])  # for multiple actions
        action_space = gym.spaces.Discrete(2)  # 0: do nothing, 1: flap the wings
        observation_space = gym.spaces.Box(
            # low=np.array([-120, -15, -90, -265, 200, 125, 200, 515, 200, 905, 200], dtype=np.float32),
            # high=np.array([755, 19, 20, 300, 600, 510, 600, 900, 600, 1290, 600], dtype=np.float32),
            low=np.array([-120, -17, 0, -650, -650], dtype=np.float32),
            high=np.array([755, 21, 500, 550, 550], dtype=np.float32),
            dtype=np.float32
        )

        return action_space, observation_space

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
            if event.type == QUIT:
                pygame.quit()
                sys.exit()

        self.background.tick()
        self.pipes.tick()
        self.floor.tick()
        self.player.tick()
        self.score.tick()

        reward = self.calculate_reward(action=action, died=terminated, passed_pipe=passed_pipe)

        pygame.display.update()
        self.config.tick()

        return self.get_state(), reward, terminated, False

    def get_state(self):
        next_pipe_pair = next_next_pipe_pair = None
        for i, pipe in enumerate(self.pipes.upper):
            if pipe.x + pipe.w < self.player.x:
                continue

            next_pipe_pair = (pipe, self.pipes.lower[i])
            next_next_pipe_pair = (self.pipes.upper[i + 1], self.pipes.lower[i + 1])
            break

        horizontal_distance_to_next_pipe = next_pipe_pair[0].x + next_pipe_pair[0].w - self.player.x
        next_pipe_vertical_center = self.get_pipe_pair_center(next_pipe_pair)[1]
        next_next_pipe_vertical_center = self.get_pipe_pair_center(next_next_pipe_pair)[1]

        vertical_distance_to_next_pipe_center = self.player.cy - next_pipe_vertical_center
        vertical_distance_to_next_next_pipe_center = self.player.cy - next_next_pipe_vertical_center

        distances_to_pipe = [horizontal_distance_to_next_pipe,
                             vertical_distance_to_next_pipe_center,
                             vertical_distance_to_next_next_pipe_center
                             ]

        game_state = np.array([self.player.y, self.player.vel_y] + distances_to_pipe, dtype=np.float32)
        return game_state

    def calculate_reward(self, action, died, passed_pipe) -> int:
        reward = 0
        if died:
            reward -= 1000  # 400 (first 10M steps was 400, then 1000)
        else:
            reward += 1  # 2
        if passed_pipe:
            reward += 100  # 200
        if action == 1:
            reward -= 0.2  # 0.5

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
