from typing import Tuple

import pygame

from ..utils import GameConfig, GameState, GameStateManager
from .entity import Entity


class AttributeBar(Entity):
    def __init__(
        self,
        config: GameConfig,
        gsm: GameStateManager,
        x: int,
        y: int,
        w: int,
        h: int = 10,
        max_value: int = 100,
        color: Tuple[int, int, int] = (255, 0, 0),
        bg_color: Tuple[int, int, int] = None
    ) -> None:
        super().__init__(config, None, x, y, w, h)
        self.gsm = gsm
        self.max_value = max_value
        self.current_value = max_value
        self.color = color
        self.bg_color = bg_color or tuple([int(channel * 0.4) for channel in color])
        self.update_bar_surface()

    def change_value(self, amount) -> None:
        if amount == 0:
            return

        previous_value = self.current_value
        self.current_value += amount
        self.current_value = pygame.math.clamp(self.current_value, 0, self.max_value)

        if previous_value != self.current_value:
            self.update_bar_surface()

    def set_value(self, value) -> None:
        if value == self.current_value:
            return
        previous_value = self.current_value
        self.current_value = pygame.math.clamp(value, 0, self.max_value)

        if previous_value != self.current_value:
            self.update_bar_surface()

    def is_empty(self) -> bool:
        return self.current_value <= 0

    def draw(self) -> None:
        if self.gsm.get_state() == GameState.START:
            return

        super().draw()

    def update_bar_surface(self) -> None:
        value_ratio = self.current_value / self.max_value
        current_width = int(self.w * value_ratio)

        self.image = pygame.Surface((self.w, self.h), pygame.SRCALPHA)

        pygame.draw.rect(self.image, self.bg_color, (0, 0, self.w, self.h))
        pygame.draw.rect(self.image, self.color, (0, 0, current_width, self.h))
