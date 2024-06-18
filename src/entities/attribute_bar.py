from typing import Tuple

import pygame

from ..utils import GameConfig, GameState, GameStateManager, printc
from .entity import Entity


class AttributeBar(Entity):
    def __init__(
        self,
        config: GameConfig,
        x: int,
        y: int,
        w: int,
        h: int = 10,
        max_value: int = 100,
        color: Tuple[int, int, int, int] = (255, 0, 0, 255),
        bg_color: Tuple[int, int, int, int] = None,
        gsm: GameStateManager = None
    ) -> None:
        super().__init__(config, None, x, y, w, h)
        if gsm is None:
            gsm = GameStateManager()
            gsm.set_state(GameState.PLAY)
        self.gsm = gsm
        self.max_value = max_value
        self.current_value = max_value
        self.color = color + (255,) if len(color) == 3 else color
        if bg_color is not None:
            self.bg_color = bg_color + (color[3],) if len(bg_color) == 3 else bg_color
        else:
            self.bg_color = tuple([int(channel * 0.4) for channel in color[:3]] + [self.color[3]])
        if self.color[3] != self.bg_color[3]:
            printc("The alpha channel of bg_color will be ignored. "
                   "Current implementation uses the alpha channel of 'color' for the entire bar.", color="yellow")
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
        self.image.set_alpha(self.color[3])

        pygame.draw.rect(self.image, self.bg_color, (0, 0, self.w, self.h))
        pygame.draw.rect(self.image, self.color, (0, 0, current_width, self.h))
