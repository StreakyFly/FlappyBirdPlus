import pygame

from .gun import Gun


class Deagle(Gun):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.offset = pygame.Vector2(30, 20)
        self.pivot = pygame.Vector2(self.w * 0.42, self.h * 0.5)
        self.barrel_end_pos = pygame.Vector2(self.w, self.h * 0.1875)
        self.update_position()
