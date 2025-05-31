import pygame

from .gun import Gun
from .ammo import MediumBullet
from ..item import ItemName


class Deagle(Gun):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.set_properties(
            ammo_name=ItemName.BULLET_MEDIUM,
            ammo_class=MediumBullet,
            damage=85,
            ammo_speed=52,
            magazine_size=7,
            shoot_cooldown=28,
            reload_cooldown=63
        )
        self.set_positions(
            offset=pygame.Vector2(30, 20),
            pivot=pygame.Vector2(25, 20),  # self.w * 0.42, self.h * 0.5
            barrel_end_pos=pygame.Vector2(60, 8)  # self.w, self.h * 0.1875 (round it up as it looks better)
        )
        self.set_recoil(
            distance=16,
            duration=5,
            rotation=18
        )
