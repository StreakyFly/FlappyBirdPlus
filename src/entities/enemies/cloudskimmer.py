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

        self.set_max_hp(300)

        self.rotation = random.randint(-30, 50)

        self.gun: Union[Gun, Item] = None

    def tick(self):
        if self.running:
            self.time += 1
            self.x += self.vel_x
            self.sin_y = self.amplitude * math.sin(self.frequency * self.time)
            self.y = self.initial_y + self.sin_y
        self.gun.tick()

        if self.running:
            self.gun.use(0)  # TODO only for testing, later the shooting and aiming will be controlled by an AI agent
        super().tick()

    def stop(self) -> None:
        for bullet in self.gun.shot_bullets:
            bullet.stop()
        super().stop()

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

        # second argument is ammo item - it doesn't really matter which item it is,
        #  as we just need an object with quantity attribute -.-
        weapons = [(ItemName.WEAPON_AK47, self.item_initializer.init_item(ItemName.EMPTY), 900, (-30, 10)),
                   (ItemName.WEAPON_DEAGLE, self.item_initializer.init_item(ItemName.EMPTY), 210, (0, 20)),
                   (ItemName.WEAPON_AK47, self.item_initializer.init_item(ItemName.EMPTY), 900, (-30, 10))]

        for pos, (weapon, ammo_item, ammo_quantity, weapon_offset) in zip(positions, weapons):
            member = CloudSkimmer(self.config, x=pos[0], y=pos[1])
            gun: Union[Item, Gun] = self.item_initializer.init_item(weapon, member)
            gun.flip()
            gun.update_offset(weapon_offset)
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
