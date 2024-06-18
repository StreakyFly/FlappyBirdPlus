import numpy as np


def get_state(player, pipes, get_pipe_pair_center: callable):
    next_pipe_pair = next_next_pipe_pair = None
    for i, pipe in enumerate(pipes.upper):
        if pipe.x + pipe.w < player.x:
            continue

        next_pipe_pair = (pipe, pipes.lower[i])
        next_next_pipe_pair = (pipes.upper[i + 1], pipes.lower[i + 1])
        break

    horizontal_distance_to_next_pipe = next_pipe_pair[0].x + next_pipe_pair[0].w - player.x
    next_pipe_vertical_center = get_pipe_pair_center(next_pipe_pair)[1]
    next_next_pipe_vertical_center = get_pipe_pair_center(next_next_pipe_pair)[1]

    vertical_distance_to_next_pipe_center = player.cy - next_pipe_vertical_center
    vertical_distance_to_next_next_pipe_center = player.cy - next_next_pipe_vertical_center

    distances_to_pipe = [horizontal_distance_to_next_pipe,
                         vertical_distance_to_next_pipe_center,
                         vertical_distance_to_next_next_pipe_center
                         ]

    game_state = np.array([player.y, player.vel_y] + distances_to_pipe, dtype=np.float32)
    return game_state
