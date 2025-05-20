import random
from collections.abc import Callable
from enum import Enum
from typing import List, Optional

import pygame

from .attribute_bar import AttributeBar
from .entity import Entity
from .floor import Floor
from .items import SpawnedItem
from .particles import ParticleManager
from .pipe import Pipe, Pipes
from ..utils import GameConfig, GameStateManager, Animation


# MAYBE ALSO ADD HUNGER BAR??
# food can of course be collected as a special "item" that is instantly used and not put in inventory
# food is like uhh food. You slowly become hungry and when you get down to 20%, the bird
# doesn't jump as high but still falls as fast, when you run out of food, it starts taking damage - very original


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

        self.mode = PlayerMode.SHM
        self.invincibility_frames = 0
        self.set_mode(PlayerMode.SHM)
        self.gsm = gsm
        # self.hp_manager = AttributeBar(config=config, gsm=gsm, max_value=100, color=(255, 0, 0, 222),
        self.hp_manager = AttributeBar(config=config, gsm=gsm, max_value=500, color=(255, 0, 0, 222),
                                       x=self.x, y=int(self.y) - 25, w=self.w, h=10)
        # self.shield_manager = AttributeBar(config=config, gsm=gsm, max_value=100, color=(20, 50, 255, 222),
        self.shield_manager = AttributeBar(config=config, gsm=gsm, max_value=500, color=(20, 50, 255, 222),
                                           x=self.x, y=int(self.y) - 40, w=self.w, h=10)
        self.particle_manager = ParticleManager(config=config)

        self.tick_train: Optional[Callable] = None

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
            self.reset_vals_train()

    def reset_vals_normal(self) -> None:
        self.vel_y = -16.875  # player's velocity along Y axis
        self.max_vel_y = 19  # 18.75  # max vel along Y, max descend speed
        self.min_vel_y = -15  # min vel along Y, max ascend speed
        self.acc_y = 1.875  # players downward acceleration

        self.rotation = 80  # player's current rotation
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

    def reset_vals_train(self) -> None:
        self.vel_y = 0  # player's velocity along Y axis
        self.max_vel_y = 0  # max vel along Y, max descend speed
        self.min_vel_y = 0  # min vel along Y, max ascend speed
        self.acc_y = 0  # players downward acceleration

        self.rotation = random.randint(-90, 20)  # player's current rotation
        self.vel_rot = 0  # player's rotation speed
        self.rot_min = -90  # player's min rotation angle
        self.rot_max = 20  # player's max rotation angle

        self.flap_acc = 0  # players speed on flapping
        self.flapped = False  # True when player flaps

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

    def tick_crash(self) -> None:
        if self.min_y <= self.y <= self.max_y:
            self.y = pygame.math.clamp(self.y + self.vel_y, self.min_y, self.max_y)
            # rotate only when it's a pipe crash and bird is still falling
            if self.crash_entity != "floor":
                self.rotate()

        # player velocity change
        if self.vel_y < self.max_vel_y:
            self.vel_y += self.acc_y

    def tick_hp(self) -> None:
        self.hp_manager.y = self.y - 25
        self.hp_manager.tick()
        self.shield_manager.y = self.y - 40
        self.shield_manager.tick()
        if self.invincibility_frames > 0:
            self.invincibility_frames -= 1
            self.change_hp(2)

    def rotate(self) -> None:
        self.rotation = pygame.math.clamp(self.rotation + self.vel_rot, self.rot_min, self.rot_max)

    def tick(self):
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

        self.tick_hp()
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
        if self.shield_manager.current_value >= amount:
            self.change_shield(-amount)
        else:
            remaining_damage = amount - self.shield_manager.current_value
            self.shield_manager.set_value(0)
            self.change_hp(-remaining_damage)

    def change_hp(self, amount: int) -> None:
        self.hp_manager.change_value(amount)

    def change_shield(self, amount: int) -> None:
        self.shield_manager.change_value(amount)

    def apply_invincibility(self, duration_frames: int = 60) -> None:
        self.invincibility_frames = duration_frames

    def set_tick_train(self, tick_train: Callable) -> None:
        self.tick_train = tick_train
