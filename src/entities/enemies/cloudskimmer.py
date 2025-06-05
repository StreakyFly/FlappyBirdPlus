import math
from typing import Union, Literal

from src.utils import GameConfig, Animation
from .enemy import Enemy, EnemyGroup
from ..items import ItemName, ItemInitializer, Item, Gun


# TODO: if bullet that hasn't bounced off a pipe, hits CloudSkimmer's gun, the gun should be destroyed/explode,
#  the CloudSkimmer should loose some HP and look scarred or maybe run away/off screen, back where it came from!
# TODO: When CloudSkimmer gets hit by the player, its face should turn angry and it could shoot faster for a while?
#  Or maybe when one of the CloudSkimmers dies, the others get angry and shoot faster?
# TODO: when one of the CloudSkimmers hits his teammate, the teammate should get angry and they should start shooting
#  at each other xD — this would only work if the CloudSkimmers hit each other VERY rarely - or maybe there could
#  be a 3% chance of this happening, so it doesn't happen too often, but still happens sometimes?
#  This would obviously be manually programmed, not done by the agent. Agent should only focus on hitting the player.

# TODO: Should there be random occasional cooldowns, so CloudSkimmers don't constantly fire?
# TODO ghosts should spawn in random colors. As they get damaged, they could change color or become more transparent.
#  When they die, the weapon should fall to the ground and the ghost should disappear.
# TODO ghosts need to be better shaded, with more detail. Possibly even have a subtle sprite animation (waves on bottom)

class CloudSkimmer(Enemy):
    def __init__(self, config: GameConfig, pos_id, amplitude, stop_dist, slow_dist, *args, **kwargs):
        super().__init__(config, Animation(config.images.enemies['cloudskimmer']), *args, **kwargs)
        self.eyes = config.images.enemies['cloudskimmer-eyes'][0]
        self.id: Literal[0, 1, 2] = pos_id  # 0: top, 1: middle, 2: bottom (unless the group is changed)
        # should they start at different times? Maybe CloudSkimmerGroup picks a random time, and then each member
        #  starts at a different time from that point within a certain range
        self.time = 0  #random.randint(0, 21)  # period of sin wave = 2 * pi / frequency = 2 * pi / 0.15 = 41.8879
        self.initial_y = self.y
        self.vel_x = -8
        self.initial_vel_x = self.vel_x
        self.amplitude = amplitude  # oscillation amplitude
        self.stop_distance = stop_dist  # distance at which the cloudskimmer stops
        self.slow_down_distance = slow_dist  # distance at which the cloudskimmer starts slowing down
        self.frequency = 0.15  # oscillation frequency
        self.sin_y = 0  # sin wave vertical position

        self.set_max_hp(200)

        self.gun: Union[Gun, Item] = None
        self.gun_rotation = 0
        self.gun_rotation_speed = 3  # Too low (like 3) and rotation becomes too slow to do sick trickshots in time,
                                     # too high and the agent can't aim precisely.
                                     # Continuous action space could fix this, but we'll rock with discrete for now.

    def tick(self):
        if self.running:
            self.time += 1
            self.x += self.vel_x
            self.sin_y = self.amplitude * math.sin(self.frequency * self.time)
            self.y = round(self.initial_y + self.sin_y)  # without rounding this, the gun is jittery
        super().tick()
        self.update_eyes()
        self.gun.tick()

    def stop(self) -> None:
        self.gun.stop()
        super().stop()

    def set_gun(self, gun: Union[Item, Gun], ammo_item) -> None:
        self.gun = gun
        gun.update_ammo_object(ammo_item)

    def stop_advancing(self) -> None:
        self.vel_x = 0

    def slow_down(self, total_distance: int, remaining_distance: float) -> None:
        self.vel_x = round(self.initial_vel_x * ((remaining_distance + 25) / (total_distance + 25)))  # without rounding this, the gun is jittery

    def shoot(self) -> None:
        if self.x > 800:  #670:  # if the enemy is not on the screen yet, don't shoot
            return
        self.gun.use(0)

    def reload(self) -> None:
        self.gun.use(1)

    def rotate_gun(self, action: int = 0) -> None:  # 0: do nothing, 1: rotate up, 2: rotate down
        # TODO try to smooth this out if it looks too jittery after training (rotation smoothing - inertia)
        if action == 0:
            return
        elif action == 1:
            self.gun_rotation -= self.gun_rotation_speed
        elif action == 2:
            self.gun_rotation += self.gun_rotation_speed

        self.gun_rotation = max(min(self.gun_rotation, 60), -60)  # ensure rotation stays within bounds

    def update_eyes(self):
        """
        Draws the ghost's eyes on the screen.
        The vertical offset is interpolated based on gun rotation.
        """
        max_offset = 5
        vertical_offset = (self.gun_rotation / 60) * max_offset
        self.config.screen.blit(self.eyes, (self.x, self.y + vertical_offset))


class CloudSkimmerGroup(EnemyGroup):
    def __init__(self, config: GameConfig, x: int, y: int, env, *args, **kwargs):
        self.env = env
        self.item_initializer = ItemInitializer(config, env=env)
        self.x_gap = 90  # gap between some members in the group
        super().__init__(config, x, y, *args, **kwargs)
        self.in_position = False
        # self.STOP_DISTANCE = 540
        # self.SLOW_DOWN_DISTANCE = 710

    def spawn_members(self) -> None:
        positions = [(self.x + self.x_gap, self.y - 125),
                     (self.x, self.y),
                     (self.x + self.x_gap, self.y + 125)]

        distances = [(540, 710),
                     (540 - self.x_gap, 710 - self.x_gap),
                     (540, 710)]

        amplitudes = [18, 15, 18]

        # second argument is ammo item - it doesn't really matter which item it is,
        #  as we just need an object with quantity attribute -.-
        weapons = [(ItemName.WEAPON_AK47, self.item_initializer.init_item(ItemName.EMPTY), 900, (-30, 35)),
                   (ItemName.WEAPON_DEAGLE, self.item_initializer.init_item(ItemName.EMPTY), 210, (-13, 35)),
                   (ItemName.WEAPON_AK47, self.item_initializer.init_item(ItemName.EMPTY), 900, (-30, 35))]

        for i, ((px, py), (stop_dist, slow_dist), amplitude, weapon_info) in enumerate(zip(positions, distances, amplitudes, weapons)):
            weapon, ammo_item, ammo_quantity, weapon_offset = weapon_info
            member = CloudSkimmer(self.config, x=px, y=py, pos_id=i, amplitude=amplitude, stop_dist=stop_dist, slow_dist=slow_dist)
            gun: Union[Item, Gun] = self.item_initializer.init_item(weapon, member)
            gun.flip()
            gun.update_offset(weapon_offset)
            ammo_item.quantity = ammo_quantity
            member.set_gun(gun, ammo_item)
            self.members.append(member)

    def tick(self):
        if self.in_position:
            pass
        else:
            # THIS LOGIC IS NOT OK, because if the members[0] dies before reaching the position, second member's position
            # will be taken into account instead, which will cause the group to stop at different position than intended
            # if self.members and self.members[0].x < self.SLOW_DOWN_DISTANCE:
            #     for member in self.members:
            #         member.slow_down(self.SLOW_DOWN_DISTANCE - self.STOP_DISTANCE, self.members[0].x - self.STOP_DISTANCE)
            #     if self.members[0].x < self.STOP_DISTANCE:
            #         self.in_position = True
            #         for member in self.members:
            #             member.stop_advancing()

            # Quick "fix" for the above logic - we simply put specific distances for each member,
            #  so it doesn't matter which one's x position we check, they will all slow down & stop at the same position
            if self.members and self.members[0].x < self.members[0].slow_down_distance:
                for member in self.members:
                    member.slow_down(self.members[0].slow_down_distance - self.members[0].stop_distance, self.members[0].x - self.members[0].stop_distance)
                if self.members[0].x < self.members[0].stop_distance:
                    self.in_position = True
                    for member in self.members:
                        member.stop_advancing()

        super().tick()
