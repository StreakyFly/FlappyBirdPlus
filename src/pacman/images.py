from typing import Tuple

import pygame

from src.utils import load_image, animation_spritesheet_to_frames


class Images:
    background: pygame.Surface
    player: Tuple[pygame.Surface, ...]
    enemy: Tuple[pygame.Surface, ...]

    def __init__(self, player_id: int):
        self._load_base_images()
        self._load_player(player_id)

    def _load_base_images(self):
        pass

    def _load_player(self, player_id: int):
        PLAYER_IMG_NAMES = ('bird-yellow', 'bird-blue', 'bird-red')
        player_spritesheet = load_image(f'pacman/{PLAYER_IMG_NAMES[player_id]}', True)
        self.player = tuple(animation_spritesheet_to_frames(player_spritesheet, 3))
