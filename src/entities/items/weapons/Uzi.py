import pygame

from .gun import Gun
from .ammo import SmallBullet
from ..item import ItemName


class Uzi(Gun):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.set_properties(
            ammo_name=ItemName.BULLET_SMALL,
            ammo_class=SmallBullet,
            damage=17,
            ammo_speed=25,
            magazine_size=32,
            shoot_cooldown=int(self.config.fps * 0.1),
            reload_cooldown=int(self.config.fps * 2)
        )
        self.set_positions(
            offset=pygame.Vector2(20, 10),
            pivot=pygame.Vector2(self.w * 0.5, self.h * 0.45),
            barrel_end_pos=pygame.Vector2(self.w, self.h * 0.35)
        )
        self.set_recoil(
            distance=10,
            duration=4,
            rotation=9
        )
