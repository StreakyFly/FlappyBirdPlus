import random
from typing import Tuple

import pygame

from src.utils import GameConfig, Animation
from src.entities import Entity


class Enemy(Entity):
    def __init__(self, config: GameConfig, enemy_sprites: Tuple[pygame.Surface, ...]):
        x = random.randint(50, 600)  # int(config.window.width * 0.2)
        y = random.randint(220, 900)  # int((config.window.height - image.get_height()) / 2)
        super().__init__(config, enemy_sprites[0], x, y)

        self.animation = Animation(images=list(enemy_sprites))

    def tick(self) -> None:
        super().tick()

    def draw(self) -> None:
        self.image = self.animation.update()
        super().draw()
