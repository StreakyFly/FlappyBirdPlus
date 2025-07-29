from collections.abc import Callable
from enum import Enum
from typing import List, Optional

import pygame

from src.utils import GameConfig, GameStateManager, Animation
from .attribute_bar import AttributeBar
from .entity import Entity
from .floor import Floor
from .items import SpawnedItem
from .particles import ParticleManager
from .pipe import Pipe, Pipes


class PlayerMode(Enum):
    SHM = "SHM"  # Simple Harmonic Motion
    NORMAL = "NORMAL"
    CRASH = "CRASH"
    TRAIN = "TRAIN"  # custom mode for training


class Player(Entity):
    def __init__(self, config: GameConfig, gsm: GameStateManager) -> None:
        image = config.images.player[0]
        x = int(config.window.width * 0.2)
        y = int((config.window.height - image.get_height()) / 2)
        super().__init__(config, image, x, y)
        self.min_y = -2 * self.h
        self.max_y = config.window.viewport_height - self.h * 0.75

        self.animation = Animation(frames=list(self.config.images.player) + [self.config.images.player[1]])

        self.crashed = False
        self.crash_entity = None
        self.flapped = False
        self.rotation = None
        self.jump_power: float = 1.0  # how high & fast the player jumps

        self.frame: int = 0
        self.invincibility_frames = 0
        self.mode = PlayerMode.SHM
        self.set_mode(PlayerMode.SHM)
        self.particle_manager = ParticleManager(config=config)
        self.tick_train: Optional[Callable] = None  # custom tick function for TRAIN mode

        self.food_bar = AttributeBar(config=config, gsm=gsm, max_value=100, color=(96, 240, 64, 232),
                                     x=self.x, y=int(self.y) - 10, w=self.w, h=10)
        self.shield_bar = AttributeBar(config=config, gsm=gsm, max_value=100, color=(20, 50, 255, 222),
                                       x=self.x, y=int(self.y) - 40, w=self.w, h=10)
        self.hp_bar = AttributeBar(config=config, gsm=gsm, max_value=100, color=(255, 0, 0, 222),
                                   x=self.x, y=int(self.y) - 25, w=self.w, h=10)

    def set_mode(self, mode: PlayerMode) -> None:
        self.mode = mode
        if mode == PlayerMode.NORMAL:
            self.reset_vals_normal()
            self.config.sounds.play_random(self.config.sounds.flap)
        elif mode == PlayerMode.SHM:
            self.reset_vals_shm()
        elif mode == PlayerMode.CRASH:
            self.animation.stop()
            self.config.sounds.play(self.config.sounds.hit)
            if self.crash_entity == "pipe":
                self.config.sounds.play(self.config.sounds.die)
            self.reset_vals_crash()
        elif mode == PlayerMode.TRAIN:
            self.reset_vals_still()

    def reset_vals_normal(self) -> None:
        self.vel_y = -16.875  # player's velocity along Y axis
        self.max_vel_y = 19  # 18.75  # max vel along Y, max descend speed
        self.min_vel_y = -15  # min vel along Y, max ascend speed
        self.acc_y = 1.875  # players downward acceleration

        self.rotation = 20  # 80 <-- why was 80 here??  # player's current rotation
        self.vel_rot = -2.7  # player's rotation speed
        self.rot_min = -90  # player's min rotation angle
        self.rot_max = 20  # player's max rotation angle

        self.flap_acc = -16.875  # players speed on flapping
        self.flapped = False  # True when player flaps

    def reset_vals_shm(self) -> None:
        self.vel_y = 1.875  # player's velocity along Y axis
        self.max_vel_y = 7.5  # max vel along Y, max descend speed
        self.min_vel_y = -7.5  # min vel along Y, max ascend speed
        self.acc_y = 0.9375  # players downward acceleration

        self.rotation = 0  # player's current rotation
        self.vel_rot = 0  # player's rotation speed
        self.rot_min = 0  # player's min rotation angle
        self.rot_max = 0  # player's max rotation angle

        self.flap_acc = 0  # players speed on flapping
        self.flapped = False  # True when player flaps

    def reset_vals_crash(self) -> None:
        self.acc_y = 3.75
        self.vel_y = 13.125
        self.max_vel_y = 28.125
        self.vel_rot = -8

    def reset_vals_still(self) -> None:
        self.vel_y = 0  # player's velocity along Y axis
        self.max_vel_y = 0  # max vel along Y, max descend speed
        self.min_vel_y = 0  # min vel along Y, max ascend speed
        self.acc_y = 0  # players downward acceleration

        self.rotation = 0  # player's current rotation
        self.vel_rot = 0  # player's rotation speed
        self.rot_min = -90  # player's min rotation angle
        self.rot_max = 20  # player's max rotation angle

        self.flap_acc = 0  # players speed on flapping
        self.flapped = False  # True when player flaps

    def set_jump_power(self, jump_power: float) -> None:
        """
        Set the jump factor, which affects how high & fast the player jumps.
        """
        self.jump_power = jump_power
        self.min_vel_y = -15 * self.jump_power
        self.vel_rot = -2.7 * self.jump_power
        self.flap_acc = -16.875 * self.jump_power

    def tick_shm(self) -> None:
        if self.vel_y >= self.max_vel_y or self.vel_y <= self.min_vel_y:
            self.acc_y *= -1
        self.vel_y += self.acc_y
        self.y += self.vel_y

    def tick_normal(self) -> None:
        if self.vel_y < self.max_vel_y and not self.flapped:
            self.vel_y += self.acc_y
        if self.flapped:
            self.flapped = False

        self.y = pygame.math.clamp(self.y + self.vel_y, self.min_y, self.max_y)
        self.rotate()
        self.tick_food()

    def tick_crash(self) -> None:
        if self.min_y <= self.y <= self.max_y:
            self.y = pygame.math.clamp(self.y + self.vel_y, self.min_y, self.max_y)
            # rotate only when it's a pipe crash and bird is still falling
            if self.crash_entity != "floor":
                self.rotate()

        # player velocity change
        if self.vel_y < self.max_vel_y:
            self.vel_y += self.acc_y

    def tick_food(self) -> None:
        """
        Drains food, heals/damages player, and adjusts its jump power based on food level.
        """
        # how often to remove 1 food
        drain_interval = 30  # normal: drain every 1 second

        # heal player when high food and HP is not full
        if self.food_bar.current_value >= 80 and self.hp_bar.current_value < self.hp_bar.max_value:
            if self.frame % 9 == 0:  # heal every 0.3 sec
                self.hp_bar.change_value_by(1)
            drain_interval = 15  # faster drain while healing (1 food every 0.5 sec)
        # drain food slowly when food is low
        elif self.food_bar.current_value <= 20:
            drain_interval = 45  # slower drain (1 food every 1.5 sec)
            # linearly decrease jump power
            factor = 0.75 + 0.25 * (self.food_bar.current_value / 20)
            self.set_jump_power(factor)  # weaker jump (0.75 - 1.0)

        # restore jump power when food is high enough
        if self.jump_power < 1.0 and self.food_bar.current_value > 20:
            self.set_jump_power(1.0)

        # damage player when food is at 0
        if self.food_bar.current_value <= 0 and self.frame % 15 == 0:
            self.hp_bar.change_value_by(-1)

        # drain food at determined interval
        if self.frame % drain_interval == 0:
            self.food_bar.change_value_by(-1)

    def tick_bars(self) -> None:
        self.hp_bar.y = self.y - 25
        self.hp_bar.tick()
        self.shield_bar.y = self.y - 40
        self.shield_bar.tick()
        self.food_bar.y = self.y - 55
        self.food_bar.tick()

    def rotate(self) -> None:
        self.rotation = pygame.math.clamp(self.rotation + self.vel_rot, self.rot_min, self.rot_max)

    def tick(self):
        self.frame += 1

        match self.mode:
            case PlayerMode.SHM:
                self.tick_shm()
            case PlayerMode.NORMAL:
                self.tick_normal()
            case PlayerMode.CRASH:
                self.tick_crash()
            case PlayerMode.TRAIN:
                if self.tick_train is not None:
                    self.tick_train()

        if self.invincibility_frames > 0:
            self.invincibility_frames -= 1
            self.hp_bar.change_value_by(2)

        self.tick_bars()
        self.particle_manager.tick()
        super().tick()

    def draw(self) -> None:
        self.image = self.animation.update()
        # self.update_image(self.animation.update())

        rotated_image = pygame.transform.rotate(self.image, self.rotation)
        rotated_rect = rotated_image.get_rect(center=self.rect.center)
        self.config.screen.blit(rotated_image, rotated_rect)

    def flap(self) -> None:
        if self.y > self.min_y:
            self.vel_y = self.flap_acc
            self.flapped = True
            self.rotation = self.rot_max
            self.config.sounds.play_random(self.config.sounds.flap)

    def crossed(self, pipe: Pipe) -> bool:
        return pipe.cx <= self.cx < pipe.cx - pipe.vel_x

    def handle_bad_collisions(self, pipes: Pipes, floor: Floor) -> None:
        if self.invincibility_frames > 0:
            return

        if self.collide(floor):
            self.crashed = True
            self.crash_entity = "floor"
            self.deal_damage(3)

        for pipe in pipes.upper + pipes.lower:
            # TODO: add a short grace period - if player collides/bumps into the pipe at the top/bottom edge, and
            #  stops colliding with it within a few frames (2-3), don't crash it, maybe just add some scratch particles,
            #  deal a small amount of damage, and somehow bounce the player off the pipe (downwards/upwards).
            #  But if the player rams into the pipe directly, then immediately crash it.
            if self.collide(pipe):
                self.crashed = True
                self.crash_entity = "pipe"
                self.deal_damage(200)

    def collided_items(self, spawned_items: List[SpawnedItem]) -> List[SpawnedItem]:
        """returns spawned item(s) if player collides with them"""
        items = []
        for item in spawned_items:
            if self.collide(item):
                # Spawn particles when player collects the item
                self.particle_manager.spawn_particles(
                    item.cx, item.cy, count=(8, 12),
                    lifespan=(15, 25),
                    radius=(12, 20),
                    gravity=(0.07, 0.14),
                    position_offset_x=(-40, 40),
                    position_offset_y=(-40, 40),
                    initial_velocity_x=(-5+item.vel_x+1, 5+item.vel_x+1),  # take item's velocity into account (partly)
                    initial_velocity_y=(-5, 5),
                    color=(178, 245, 247, (150, 220))
                )
                items.append(item)
        return items

    def deal_damage(self, amount: int) -> None:
        if self.invincibility_frames > 0:
            return

        if self.shield_bar.current_value >= amount:
            self.shield_bar.change_value_by(-amount)
        else:
            remaining_damage = amount - self.shield_bar.current_value
            self.shield_bar.set_value(0)
            self.hp_bar.change_value_by(-remaining_damage)

    def apply_invincibility(self, duration_frames: int = 60) -> None:
        self.invincibility_frames = duration_frames

    def set_tick_train(self, tick_train: Callable) -> None:
        self.tick_train = tick_train
