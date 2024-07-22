import sys
import numpy as np
import gymnasium as gym

import pygame
from pygame import QUIT

from .base_env import BaseEnv


class AdvancedFlappyEnv(BaseEnv):
    def __init__(self):
        super().__init__()

    def get_action_and_observation_space(self):
        # TODO implement this function
        print("ERROR: get_action_and_observation_space() is not implemented yet.")
        return False

    def perform_step(self, action):
        # TODO implement this function
        print("ERROR: perform_step() is not implemented yet.")
        return False

    def get_observation(self):
        # TODO implement this function
        print("ERROR: get_observation() is not implemented yet.")
        return False

    def calculate_reward(self) -> int:
        # TODO implement this method
        print("ERROR: calculate_reward() is not implemented yet.")
        return False
