import random
from typing import Tuple

import pygame


class Images:
    background: pygame.Surface
    floor: pygame.Surface
    pipe: Tuple[pygame.Surface, pygame.Surface]
    player: Tuple[pygame.Surface, pygame.Surface, pygame.Surface]
    welcome_message: pygame.Surface
    game_over: pygame.Surface

    def __init__(self) -> None:
        self.background = _load_image('background-day.png').convert()
        self.floor = _load_image('floor.png').convert_alpha()
        self.pipe = (pygame.transform.flip(_load_image('pipe.png').convert_alpha(), False, True),
                     _load_image('pipe.png').convert_alpha())
        self.welcome_message = _load_image('welcome_message.png').convert_alpha()
        self.game_over = _load_image('game_over.png').convert_alpha()
        self.randomize()

    def randomize(self) -> None:
        PLAYER_IMGS = [['yellowbird-upflap.png', 'yellowbird-midflap.png', 'yellowbird-downflap.png'],
                       ['bluebird-upflap.png', 'bluebird-midflap.png', 'bluebird-downflap.png'],
                       ['redbird-upflap.png', 'redbird-midflap.png', 'redbird-downflap.png']]

        random_player = random.randint(0, len(PLAYER_IMGS) - 1)

        self.player = (_load_image(f'birds/{PLAYER_IMGS[random_player][0]}'),
                       _load_image(f'birds/{PLAYER_IMGS[random_player][1]}'),
                       _load_image(f'birds/{PLAYER_IMGS[random_player][2]}'))


def _load_image(path):
    return pygame.image.load(f'assets/images/{path}')
