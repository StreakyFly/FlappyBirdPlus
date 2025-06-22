import math
import random
from typing import Optional, Literal

import numpy as np
import pygame

from src.entities import Player, ItemName
from src.utils import GameConfig, Animation
from .enemy import Enemy, EnemyGroup


# Tiny birds/enemies with spiky beak or whatever in front, blazingly fast, fly through the player and cause damage
# attack in groups, 2-4 at once. First they slowly arrive on the screen in the top right corner, slow down, wait a bit,
# and then one by one they start flying towards the player, with small delay after each one.

# TODO: Make them different colors, and then simply choose a random color for each one.

class SkyDart(Enemy):
    heal_on_kill = 15  # reward the player with 15 shield when they kill a CloudSkimmer

    def __init__(self, config: GameConfig, stop_dist: int, slow_dist: int, *args, **kwargs):
        super().__init__(
            config=config,
            animation=Animation(config.images.enemies['skydart'] + [config.images.enemies['skydart'][1]]),
            possible_drop_items=[
                ItemName.FOOD_APPLE,  # Food (apples are the only food SkyDarts eat)
                ItemName.POTION_HEAL, ItemName.POTION_SHIELD,  # Potions (they have no idea what potions are, but the bottles are shiny!)
                ItemName.HEAL_BANDAGE,  # Heals (they like playing with bandages)
                ItemName.TOTEM_OF_UNDYING  # Special (SHINY!!)
            ],
            *args, **kwargs
        )
        self.id: Literal[0, 1, 2, 3]
        self.set_max_hp(30)

        self.stop_distance = stop_dist  # distance at which the SkyDart stops
        self.slow_down_distance = slow_dist  # distance at which the SkyDart starts slowing down
        self.in_position: bool = False  # whether the bird is in position to launch

        self.vel_x = -8
        self.vel_y = 0
        self.initial_vel_x = self.vel_x

        self.target: Optional[Player] = None
        self.launched: bool = False
        self.damaged_target: bool = False

        # flight parameters
        self.g_effect: float = 1.32  # gravity strength
        self.speed: float = 12.0  # initial launch speed (pixels per frame)
        self.segments: list[tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]] = []  # cubic bezier segments for flight path
        self.seg_index: int = 0  # current segment index
        self.t_on_seg: float = 0.0  # parameter t for cubic bezier segments, starts at 0 and goes to 1
        self.target_is_above: bool = False  # whether the target is above the bird

    def tick(self):
        if self.running:
            if self.target is None:
                if not self.in_position:
                    self.x += self.vel_x
                    self.y += self.vel_y
                    if self.x < self.slow_down_distance:
                        self.slow_down()
                        if self.x < self.stop_distance:
                            self.in_position = True
                            self.stop_advancing()
            else:
                self.update_dive()

            self.check_target_collision()
        super().tick()

    def draw(self) -> None:
        self.config.screen.blit(pygame.transform.rotate(self.image, self.rotation), self.rect)

    def stop_advancing(self) -> None:
        self.vel_x = 0

    def slow_down(self) -> None:
        total_distance = self.slow_down_distance - self.stop_distance
        remaining_distance = self.x - self.stop_distance
        self.vel_x = round(self.initial_vel_x * ((remaining_distance + 32) / (total_distance + 32)))  # +32 just felt right, no particular reason for it

    def update_dive(self) -> None:
        p0,p1,p2,p3 = self.segments[self.seg_index]

        # tangent & unit direction on current segment
        tangent = self._cubic_d(p0,p1,p2,p3, self.t_on_seg)
        arc_len = float(np.linalg.norm(tangent))
        direction = tangent / arc_len

        # gravity-style acceleration
        dive_ang = math.atan2(direction[1], direction[0])
        if not self.target_is_above:
            self.speed += self.g_effect * math.sin(dive_ang) * 0.5
        else:
            self.speed += self.g_effect * 0.1  # yes, gravity is working upside down if target is above, makes complete sense, yes
        self.speed = max(self.speed, 12)

        # advance param so we travel exactly self.speed px
        dt = self.speed / arc_len
        self.t_on_seg += dt

        # move to new point
        new_pos = self._cubic(p0,p1,p2,p3, min(1.0, self.t_on_seg))
        self.vel_x = new_pos[0] - self.x
        self.vel_y = new_pos[1] - self.y
        self.x, self.y = new_pos

        # if current segment is done, move to the next one
        if self.t_on_seg >= 1.0:
            self.seg_index += 1
            self.t_on_seg -= 1.0  # reset t_on_seg for the next segment (takes into account the remainder/overflow)

        self.rotation = math.degrees(math.atan2(self.vel_x, self.vel_y)) + 90

    def launch(self, target: Player) -> None:
        """
        Launch the SkyDart towards the target player.

        PREPARE A FLIGHT PATH (nice cubic Bézier curve)
        If you want to adjust this, I would suggest you first ask Mr. ChatGPT to draw a graph of curves for you.
        Simply send him this entire launch() method and ask him to draw a graph of the cubic Bézier curves and their handles
        with the SkyDart/current position being at around (560, 90), the target x position at 144 and target y position
        at random points ∈ [0, 755], so you see what you're even dealing with, cuz you simply cannot visualize it
        just by looking at this code "thanks" to the dynamic calculation of certain points.

        This method contains a lot of hardcoded values. I just used whatever felt right at the time ☉ ‿ ⚆.
        """
        self.target = target
        self.launched = True

        target_x = target.x + random.randint(-10, 10)  # add a lil offset to the target position
        target_y = target.y + random.randint(-10, 10)  # add a lil offset to the target position

        y_dist_norm = (target_y - self.y) / 720  # normalized y distance to the target, roughly in range [0, 1]
        self.target_is_above = y_dist_norm < 0

        # --- First segment ---
        # current position
        p0 = np.array([self.x, self.y])
        # control point near start: so the bird turns downwards a bit more smoothly
        p1 = np.array([self.x - 64, self.y + 12 * y_dist_norm])
        # the smaller the y distance to the target, the closer x coordinate of this point should be to the target
        # Map [0, 720] to [0.28, ~1] linearly, 0.28 being the minimum distance (0px) and ~1 being the maximum distance (720px)
        min_y_dist_norm = 0.28
        y_offset_special = 0 if y_dist_norm > 0 else abs(y_dist_norm * 320)
        y_dist_norm_special = abs(y_dist_norm if y_dist_norm > 0 else y_dist_norm * 0.64)  # dear lord, forgive me for these variable names
        y_dist_norm_clipped = max(min_y_dist_norm, (min_y_dist_norm + y_dist_norm_special) * 0.72)
        # control point - main-ish: so the bird flies towards the target in a smooth curve
        p2 = np.array([target_x + (self.x - target_x) * y_dist_norm_clipped, target_y + y_offset_special])
        # target position
        p3 = np.array([target_x, target_y])

        # --- Second segment ---
        # The closer to the floor the target is, the more the bird should turn up when it reaches the target
        # - if the target is roughly on the same level as the bird, the bird should continue flying roughly straight,
        # - if the target is above the bird, the bird should continue flying roughly in the same direction upwards.
        # Basically, the bird will never go down after reaching the target, it will either go straight or up.
        y_offset = -120 * y_dist_norm if not self.target_is_above else 600 * y_dist_norm
        # off-screen waypoint
        p6 = np.array([-240, p3[1] + y_offset])
        # control points
        p4 = p3 + 0.56 * (p3 - p2)
        p5 = p6 - 0.3 * (p6 - p3) + np.array([0, 32 * y_dist_norm])

        self.segments = [(p0, p1, p2, p3), (p3, p4, p5, p6)]
        self.speed = 12 + 3 * (1 - max(0, y_dist_norm))

    def check_target_collision(self):
        if self.damaged_target:
            return

        if self.target is not None and self.collide(self.target):
            self.damaged_target = True
            self.target.deal_damage(30)
            self.config.sounds.play(self.config.sounds.hit_quiet)

    @staticmethod
    def _cubic(p0,p1,p2,p3,t):
        return (1-t)**3*p0 + 3*(1-t)**2*t*p1 + 3*(1-t)*t**2*p2 + t**3*p3

    @staticmethod
    def _cubic_d(p0,p1,p2,p3,t):
        return 3*(1-t)**2*(p1-p0) + 6*(1-t)*t*(p2-p1) + 3*t**2*(p3-p2)


"""
Initial idea, although the implementation slightly differs from this:
1. spawn a few SkyDarts in a group at the top right corner of the screen
2. make them slowly move on screen while looking forward
3. short dramatical pause as they hover in the air
4. suddenly they all shift their eyes towards the player  // not doing this yet, maybe later
5. then one by one they start flying towards the player, with smaller delay after each one
   (those in front/closer to the player should be "launched" first)
Path to the target should be calculated just before the launch of each SkyDart (function in SkyDart that receives player's position)
Then as the bird flies towards the player, the path could be slightly adjusted, but not too much. // nope, we're not doing this
The bird should start turning up when getting close to the floor, so it doesn't crash into it.
"""
class SkyDartGroup(EnemyGroup):
    def __init__(self, config: GameConfig, x: int, y: int, target: Player, *args, **kwargs):
        super().__init__(config, x, y, *args, **kwargs)
        self.target = target  # to get player's position in order to target them
        self.cooldown = 32
        self.initial_cooldown = self.cooldown

    def spawn_members(self) -> None:
        positions = self.get_random_formation(self.x, self.y)

        for i, (x, y, stop_dist, slow_dist) in enumerate(positions):
            member = SkyDart(self.config, x=x, y=y, instance_id=i, stop_dist=stop_dist, slow_dist=slow_dist)
            self.members.append(member)

    def tick(self):
        if all(member.in_position for member in self.members) and not all(member.launched for member in self.members):
            self.cooldown -= 1
            if self.cooldown <= 0:
                self.cooldown = self.initial_cooldown
                closest_member = None
                closest_distance = float('inf')

                for member in self.members:
                    if member.launched:
                        continue
                    distance = math.sqrt((member.x - self.target.x) ** 2 + (member.y - self.target.y) ** 2)
                    if distance < closest_distance:
                        closest_distance = distance
                        closest_member = member

                if closest_member:
                    closest_member.launch(self.target)

        super().tick()

    @staticmethod
    def get_random_formation(x: int, y: int) -> list[tuple[int, int, int, int]]:
        """
        I tried a bajillion different algorithms to position these mf birbs randomly.
        Reinvented warm water 17 times, figured out how to deepfry it and then freeze it in an oven.
        Well, let me tell you one thing I noticed. It looked like complete shit. Every. Single. Time.
        I mean yeah, the entire game looks like shit. BUT THAT!? That sucked on another level.
        So I decided to hardcode a few formations that seem alright-ish.

        Rough bounds for the SkyDart positions:
        X: [400, 620] (set stop_dist to this range)
        Y: [40, 240] (set y to this range)

        [x (final), y, delay] aka.
        [stop_dist, y, further_back]:
        stop_dist: basically final X position (the distance at which the SkyDart stops)
        y: Y position (vertical position of the SkyDart)
        further_back: basically a delay before appearing on the screen (how further back/to the right the SkyDart is)
        """
        formations = [
            [[490, 60, 0], [610, 100, 70]],
            [[490, 50, 0], [550, 210, 60], [610, 120, 80]],
            [[490, 120, 0], [570, 60, 60], [590, 210, 80]],
            [[440, 100, 0], [570, 50, 60], [610, 170, 80]],
            [[420, 45, 0], [525, 80, 50], [630, 115, 100]],
            [[400, 55, 0], [510, 105, 40], [580, 40, 70], [630, 150, 75]],
            [[460, 90, 0], [510, 190, 20], [570, 40, 65], [620, 140, 70]],
        ]

        formation = random.choice(formations)

        SLOW_DOWN_LENGTH = 220  # how far from the stop distance should the birb start slowing down
        final_positions = []

        for (stop_dist, y_offset, further_back) in formation:
            final_positions.append((
                x + (stop_dist - formation[0][0]) + further_back,  # x position
                y + y_offset,                   # y position
                stop_dist,                      # stop_dist
                stop_dist + SLOW_DOWN_LENGTH    # slow_dist
            ))

        return final_positions  # [(x, y, stop_dist, slow_dist), ...for each member in the group]
