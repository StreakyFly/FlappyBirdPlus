import numpy as np

from src.entities import Player
from .base_observation import BaseObservation


class AdvancedFlappyObservation(BaseObservation):
    def __init__(self, entity: Player, env):
        super().__init__(entity, env)

    def get_observation(self):
        e = self.env

        game_state = {
            'ben': np.array([50], dtype=np.float32),
            'ten': np.array([10], dtype=np.float32),
        }

        return game_state
