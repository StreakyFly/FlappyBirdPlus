import pygame

from .gun import Gun
from .ammo import BigBullet
from ..item import ItemName


class AK47(Gun):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.set_properties(
            ammo_name=ItemName.BULLET_BIG,
            ammo_class=BigBullet,
            damage=35,
            ammo_speed=34,
            magazine_size=30,
            shoot_cooldown=6,   # int(self.config.fps * 0.23), fps being 30  <-- we don't want it tied to the fps
            reload_cooldown=84  # int(self.config.fps * 2.8), fps being 30  <-- as we're using fixed time steps
        )
        self.set_positions(
            offset=pygame.Vector2(4, 14),  # << beak; pygame.Vector2(-20, 60)  # << legs
            pivot=pygame.Vector2(39, 34),  # self.w * 0.36, self.h * 0.68
            barrel_end_pos=pygame.Vector2(110, 13)  # self.w, self.h * 0.25 (round it up as it looks better)
        )
        self.set_recoil(
            distance=15,
            duration=5,
            rotation=8
        )
