from typing import Union

import random
import math

from ...utils import GameConfig, Animation
from ..items import ItemName, ItemInitializer, Item, Gun
from .enemy import Enemy, EnemyGroup


class CloudSkimmer(Enemy):
    def __init__(self, config: GameConfig, *args, **kwargs):
        super().__init__(config, Animation(config.images.enemies['enemy-temp']), *args, **kwargs)
        self.time = 0
        self.initial_y = self.y
        self.vel_x = -8
        self.initial_vel_x = self.vel_x
        self.amplitude = 15  # oscillation amplitude
        self.frequency = 0.15  # oscillation frequency
        self.sin_y = 50  # initial relative vertical position

        self.gun: Union[Gun, Item] = None

    def tick(self):
        self.time += 1
        self.x += self.vel_x
        self.sin_y = self.amplitude * math.sin(self.frequency * self.time)
        self.y = self.initial_y + self.sin_y
        super().tick()
        self.gun.tick()
        self.gun.use(0)  # TODO only for testing, later it won't constantly shoot, but more randomly
                         #  also, it will actually aim at the player, not just fire in the same direction

    def set_gun(self, gun: Union[Item, Gun], ammo_item) -> None:
        self.gun = gun
        gun.update_ammo_object(ammo_item)

    def stop_advancing(self) -> None:
        self.vel_x = 0

    def slow_down(self, total_distance: int, remaining_distance: float) -> None:
        self.vel_x = self.initial_vel_x * ((remaining_distance + 25) / (total_distance + 25))


class CloudSkimmerGroup(EnemyGroup):
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
        weapons = [ItemName.WEAPON_AK47,
                   ItemName.WEAPON_DEAGLE,
                   ItemName.WEAPON_AK47]
        ammo = [self.item_initializer.init_item(ItemName.EMPTY),  # doesn't really matter which item,
                self.item_initializer.init_item(ItemName.EMPTY),  # we just need an object with quantity attribute
                self.item_initializer.init_item(ItemName.EMPTY)]  # -.-
        ammo_quantity = [900, 210, 900]

        for pos, weapon, ammo_item, ammo_quantity in zip(positions, weapons, ammo, ammo_quantity):
            member = CloudSkimmer(self.config, x=pos[0], y=pos[1])
            gun: Union[Item, Gun] = self.item_initializer.init_item(weapon, member)
            gun.flip()
            ammo_item.quantity = ammo_quantity
            member.set_gun(gun, ammo_item)
            self.members.append(member)

    def tick(self):
        super().tick()

        if self.in_position:
            return

        if self.members and self.members[0].x < self.SLOW_DOWN_DISTANCE:
            for member in self.members:
                member.slow_down(self.SLOW_DOWN_DISTANCE - self.STOP_DISTANCE, self.members[0].x - self.STOP_DISTANCE)
            if self.members[0].x < self.STOP_DISTANCE:
                self.in_position = True
                for member in self.members:
                    member.stop_advancing()
