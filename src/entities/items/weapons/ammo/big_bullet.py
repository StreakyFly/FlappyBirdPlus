import pygame

from .bullet import Bullet


class BigBullet(Bullet):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.bullet_offset = pygame.Vector2(-self.w, -self.h/2)
