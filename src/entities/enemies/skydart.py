import math
from typing import Union, Literal

from src.utils import GameConfig, Animation
from ..items import ItemName, ItemInitializer
from .enemy import Enemy, EnemyGroup


# Tiny birds/enemies with spiky beak or whatever in front, blazingly fast, fly through the player and cause damage
# attack in bigger groups, 4-7 at once. First they slowly arrive on the screen in the top right corner, slow down,
# wait a bit, and then one by one they start flying towards the player, with smaller delay after each one.


class SkyDart(Enemy):
    def __init__(self, config: GameConfig, *args, **kwargs):
        super().__init__(config, Animation(config.images.enemies['enemy-cloudskimmer']), *args, **kwargs)
        self.eyes = config.images.enemies['enemy-cloudskimmer-eyes'][0]
        self.time = 0
        self.initial_y = self.y
        self.vel_x = -8
        self.initial_vel_x = self.vel_x

        self.set_max_hp(150)

    def tick(self):
        if self.running:
            self.time += 1
            self.x += self.vel_x
            self.y = round(self.initial_y)
        super().tick()
        # self.update_eyes()

    def stop_advancing(self) -> None:
        self.vel_x = 0

    def slow_down(self, total_distance: int, remaining_distance: float) -> None:
        self.vel_x = round(self.initial_vel_x * ((remaining_distance + 25) / (total_distance + 25)))

    def update_eyes(self):
        """
        Draws the bird's eyes on the screen.
        The vertical offset is interpolated based on the player's position.
        """
        # max_offset = 5
        # vertical_offset = (self.gun_rotation / 60) * max_offset
        # self.config.screen.blit(self.eyes, (self.x, self.y + vertical_offset))
        pass


class SkyDartGroup(EnemyGroup):
    def __init__(self, config: GameConfig, x: int, y: int, *args, **kwargs):
        self.item_initializer = ItemInitializer(config, None)
        super().__init__(config, x, y, *args, **kwargs)
        self.in_position = False
        self.STOP_DISTANCE = 540
        self.SLOW_DOWN_DISTANCE = 710

    def spawn_members(self) -> None:
        positions = [(self.x + 90, self.y - 125),
                     (self.x, self.y),
                     (self.x + 90, self.y + 125)]

        for i, pos in enumerate(positions):
            member = SkyDart(self.config, x=pos[0], y=pos[1], pos_id=i)
            self.members.append(member)

    def tick(self):
        if self.in_position:
            pass
        else:
            if self.members and self.members[0].x < self.SLOW_DOWN_DISTANCE:
                for member in self.members:
                    member.slow_down(self.SLOW_DOWN_DISTANCE - self.STOP_DISTANCE, self.members[0].x - self.STOP_DISTANCE)
                if self.members[0].x < self.STOP_DISTANCE:
                    self.in_position = True
                    for member in self.members:
                        member.stop_advancing()

        super().tick()
