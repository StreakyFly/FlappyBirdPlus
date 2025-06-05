import numpy as np

from src.entities.player import Player
from .base_observation import BaseObservation


class BasicFlappyObservation(BaseObservation):
    def __init__(self, entity: Player, env):
        super().__init__(entity, env)

    def get_observation(self) -> np.ndarray:
        e = self.env
        next_pipe_pair = next_next_pipe_pair = None
        for i, pipe in enumerate(e.pipes.upper):
            if pipe.x + pipe.w < self.entity.x:
                continue

            next_pipe_pair = (pipe, e.pipes.lower[i])
            next_next_pipe_pair = (e.pipes.upper[i + 1], e.pipes.lower[i + 1])
            break

        horizontal_distance_to_next_pipe = next_pipe_pair[0].x + next_pipe_pair[0].w - e.player.x
        next_pipe_vertical_center = e.get_pipe_pair_center(next_pipe_pair)[1]
        next_next_pipe_vertical_center = e.get_pipe_pair_center(next_next_pipe_pair)[1]

        vertical_distance_to_next_pipe_center = e.player.cy - next_pipe_vertical_center
        vertical_distance_to_next_next_pipe_center = e.player.cy - next_next_pipe_vertical_center

        distances_to_pipe = [
            horizontal_distance_to_next_pipe,
            vertical_distance_to_next_pipe_center,
            vertical_distance_to_next_next_pipe_center
        ]

        game_state = np.array([e.player.cy, e.player.vel_y] + distances_to_pipe, dtype=np.float32)
        return game_state
