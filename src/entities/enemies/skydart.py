import math
import random
from typing import Optional

import pygame

from src.entities import Player
from src.utils import GameConfig, Animation
from .enemy import Enemy, EnemyGroup


# Tiny birds/enemies with spiky beak or whatever in front, blazingly fast, fly through the player and cause damage
# attack in bigger groups, 4-7 at once. First they slowly arrive on the screen in the top right corner, slow down,
# wait a bit, and then one by one they start flying towards the player, with smaller delay after each one.


class SkyDart(Enemy):
    def __init__(self, config: GameConfig, *args, **kwargs):
        super().__init__(config, Animation(config.images.enemies['skydart'] + [config.images.enemies['skydart'][1]]), *args, **kwargs)
        self.time = 0
        self.launch_time: int = 0
        self.set_max_hp(30)
        self.target: Optional[Player] = None
        self.target_x = None
        self.target_y = None
        self.launched: bool = False
        self.damaged_player: bool = False

        self.vel_x = -8
        self.vel_y = 0
        self.initial_vel_x = self.vel_x

    def tick(self):
        if self.running:
            self.time += 1
            if self.target is None:
                self.x += self.vel_x
            else:
                self.update_dive()
            self.check_target_collision()
        super().tick()

    def draw(self) -> None:
        self.config.screen.blit(pygame.transform.rotate(self.image, self.rotation), self.rect)

    def stop_advancing(self) -> None:
        self.vel_x = 0

    def slow_down(self, total_distance: int, remaining_distance: float) -> None:
        self.vel_x = round(self.initial_vel_x * ((remaining_distance + 25) / (total_distance + 25)))

    # TODO: update_dive() and launch() should be modified, so the bird first flies slightly more to the left
    #  and turns more and more downwards as it gets closer to the player. (It should fly in the shape of logarithmic curve from right top to left bottom)
    #  Otherwise in certain situations the SkyDart doesn't fly aggressively towards the player, but looks like it's slowing down
    #  before hitting the player, which we do not want (unless it's close to the floor, but that's a problem for later).
    def update_dive(self) -> None:
        MAX_MULTIPLIER = 1.4
        MIN_MULTIPLIER = 1.03
        time_factor = max(0.0, 1 - (self.time - self.launch_time) / 5)  # bigger multiplier at the beginning of the dive
        multiplier = MIN_MULTIPLIER + (MAX_MULTIPLIER - MIN_MULTIPLIER) * time_factor

        self.vel_x *= multiplier
        self.vel_y *= multiplier

        self.x += self.vel_x
        self.y += self.vel_y

        self.rotation = math.degrees(math.atan2(self.vel_x, self.vel_y)) + 90

    def launch(self) -> None:
        self.launched = True
        self.launch_time = self.time
        direction_x = self.target_x - self.x
        direction_y = self.target_y - self.y
        distance = math.sqrt(direction_x ** 2 + direction_y ** 2)

        if distance != 0:
            self.vel_x = -(direction_x / distance) * self.initial_vel_x
            self.vel_y = -(direction_y / distance) * self.initial_vel_x

    def set_target(self, target: Player) -> None:
        self.target = target
        offset_x = random.randint(-10, 10)
        offset_y = random.randint(-10, 10)
        self.target_x = target.x + offset_x
        self.target_y = target.y + offset_y
        self.vel_y = 2

    def check_target_collision(self):
        if self.damaged_player:
            return

        if self.target is not None and self.collide(self.target):
            self.damaged_player = True
            self.target.deal_damage(30)
            self.config.sounds.play(self.config.sounds.hit_quiet)


# TODO:
#  1. spawn a few SkyDarts in a group at the top right corner of the screen
#  2. make them slowly move on screen while looking forward
#  3. short dramatical pause as they hover in the air
#  4. suddenly they all shift their eyes towards the player
#  5. then one by one they start flying towards the player, with smaller delay after each one
#     (those in front/closer to the player should be "launched" first)
#  Path to the target should be calculated just before the launch of each SkyDart (function in SkyDart that receives player's position)
#  Then as the bird flies towards the player, the path could be slightly adjusted, but not too much.
#  The bird should start turning up when getting close to the floor, so it doesn't crash into it.
class SkyDartGroup(EnemyGroup):
    def __init__(self, config: GameConfig, x: int, y: int, target: Player, *args, **kwargs):
        super().__init__(config, x, y, *args, **kwargs)
        self.target = target  # to get player's position in order to target them
        self.in_position = False
        self.STOP_DISTANCE = 520
        self.SLOW_DOWN_DISTANCE = 710
        self.time = 0

    def spawn_members(self) -> None:
        positions = [(self.x + 90, self.y - 125),
                     (self.x, self.y),
                     (self.x + 90, self.y + 125)]

        for i, pos in enumerate(positions):
            member = SkyDart(self.config, x=pos[0], y=pos[1], pos_id=i)
            self.members.append(member)

    def tick(self):
        if self.in_position:
            self.time += 1
            # TODO: decrease the delay after each bird
            if self.time % 30 == 0:
                for member in self.members:
                    if member.launched:
                        continue
                    member.set_target(self.target)
                    member.launch()
                    break
        else:
            # fixme: if the members[0] dies before reaching the position, second member's position will be taken
            #  into account instead, which will cause the group to stop at different position than intended
            #  We did a quick fix for this in CloudSkimmerGroup, but I hate it, so we gotta come up with a better solution!
            if self.members and self.members[0].x < self.SLOW_DOWN_DISTANCE:
                for member in self.members:
                    member.slow_down(self.SLOW_DOWN_DISTANCE - self.STOP_DISTANCE, self.members[0].x - self.STOP_DISTANCE)
                if self.members[0].x < self.STOP_DISTANCE:
                    self.in_position = True
                    for member in self.members:
                        member.stop_advancing()

        super().tick()
