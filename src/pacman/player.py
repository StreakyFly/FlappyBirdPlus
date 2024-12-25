from typing import Tuple

import pygame

from src.utils import GameConfig, Animation
from src.entities import Entity


class Player(Entity):
    def __init__(self, config: GameConfig, player_sprites: Tuple[pygame.Surface, ...]):
        x = 100  # int(config.window.width * 0.2)
        y = 100  # int((config.window.height - image.get_height()) / 2)
        super().__init__(config, player_sprites[0], x, y)

        self.animation = Animation(frames=list(player_sprites) + [player_sprites[1]])

    def tick(self) -> None:
        super().tick()

    def draw(self) -> None:
        self.image = self.animation.update()
        super().draw()
