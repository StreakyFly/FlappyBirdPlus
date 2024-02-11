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
            ammo_speed=30,
            magazine_size=30,
            shoot_cooldown=int(self.config.fps * 0.25),
            reload_cooldown=int(self.config.fps * 1.5)
        )
        self.set_positions(
            offset=pygame.Vector2(4, 14),  # << beak; pygame.Vector2(-20, 60)  # << legs
            pivot=pygame.Vector2(self.w * 0.36, self.h * 0.68),
            barrel_end_pos=pygame.Vector2(self.w, self.h * 0.25)
        )
        self.set_recoil(
            distance=14,
            duration=5
        )
