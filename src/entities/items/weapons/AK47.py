import pygame

from .gun import Gun


class AK47(Gun):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.offset = pygame.Vector2(4, 14)  # beak
        # self.offset = pygame.Vector2(-20, 60)  # legs
        self.pivot = pygame.Vector2(self.w * 0.36, self.h * 0.68)  # 40, 34
        self.barrel_end_pos = pygame.Vector2(self.w, self.h * 0.25)
        self.update_position()

    # def shoot(self):
    #     super().shoot()

