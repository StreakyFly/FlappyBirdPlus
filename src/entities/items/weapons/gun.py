import math

import pygame

from ....utils import rotate_on_pivot
from ..item import Item, ItemName, ItemType


class Gun(Item):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ammo_name = None
        self.ammo_class = None
        self.damage = 0
        self.ammo_speed = 0
        self.magazine_size = 0
        self.shoot_cooldown = 0
        self.reload_cooldown = 0

        self.remaining_shoot_cooldown = 0
        self.remaining_reload_cooldown = 0
        self.quantity_after_reload = 0
        self.interaction_in_progress: bool = False

        self.offset = pygame.Vector2(0, 0)
        self.pivot = pygame.Vector2(0, 0)
        self.barrel_end_pos = pygame.Vector2(0, 0)

        self.recoil_distance = 15
        self.recoil_duration = 5
        self.recoil_remaining_duration = 0
        self.recoil_speed = self.recoil_distance / self.recoil_duration
        self.animation_offset = pygame.Vector2(0, 0)

        self.update_position()

        self.shot_bullets = set()

    def tick(self) -> None:
        self.update_position()
        self.shoot_animation()
        if len(self.shot_bullets) > 0:
            self.tick_ammo()
        super().tick()

        if not self.interaction_in_progress:
            return

        if self.remaining_shoot_cooldown == 0 and self.remaining_reload_cooldown == 0:
            self.interaction_in_progress = False
            return

        if self.remaining_shoot_cooldown > 0:
            self.remaining_shoot_cooldown -= 1

        if self.remaining_reload_cooldown > 0:
            self.remaining_reload_cooldown -= 1
            self.remaining_shoot_cooldown = 0
            if self.remaining_reload_cooldown == 0:
                self.quantity = self.quantity_after_reload

    def tick_ammo(self) -> None:
        for bullet in set(self.shot_bullets):
            # remove bullets if they are out of the game window
            extra = self.config.window.height * 0.2
            if bullet.x > self.config.window.width + extra or bullet.x < -extra or \
               bullet.y > self.config.window.height + extra or bullet.y < -extra:
                self.shot_bullets.remove(bullet)
                continue
            # TODO remove bullets if they hit enemies (if any enemy is even spawned)
            bullet.tick()

    def draw(self) -> None:
        pivot_point = pygame.Vector2(self.x + self.pivot.x, self.y + self.pivot.y)
        # pivot_point = pygame.Vector2(self.entity.x + self.pivot.x, self.entity.y + self.pivot.y)  # different weapon animation relative to the player (Ctrl+F: DWARP1)
        origin_point = self.rect.center
        rotated_image, rotated_rect = rotate_on_pivot(self.image, self.entity.rot, pivot_point, origin_point)
        self.config.screen.blit(rotated_image, rotated_rect)
        # pygame.draw.circle(self.config.screen, (255, 0, 0), self.calculate_initial_bullet_position(), 10, width=5)  # for debugging

    def update_position(self):
        self.x = self.entity.x + self.offset.x + self.animation_offset.x
        self.y = self.entity.y + self.offset.y + self.animation_offset.y

    def set_positions(self, offset: pygame.Vector2, pivot: pygame.Vector2, barrel_end_pos: pygame.Vector2) -> None:
        self.offset = offset
        self.pivot = pivot
        self.barrel_end_pos = barrel_end_pos
        self.update_position()

    def set_properties(self, ammo_name: ItemName, ammo_class: callable,damage: int, ammo_speed: int, magazine_size: int,
                       shoot_cooldown: int, reload_cooldown: int) -> None:
        self.ammo_name = ammo_name
        self.ammo_class = ammo_class
        self.damage = damage
        self.ammo_speed = ammo_speed
        self.magazine_size = magazine_size
        self.shoot_cooldown = shoot_cooldown
        self.reload_cooldown = reload_cooldown
        self.quantity_after_reload = magazine_size

    def use(self, action, ammo: Item, *args) -> None:
        if action == 0:
            self.handle_shooting(ammo)
            return
        elif action == 1:
            self.handle_reloading(ammo)
            return

    def handle_shooting(self, ammo: Item) -> None:
        if self.interaction_in_progress:
            return

        # if weapon magazine isn't empty, shoot
        if self.quantity > 0:
            self.shoot(ammo)
            return

        # if gun is empty, try reloading it
        self.handle_reloading(ammo)

    def handle_reloading(self, ammo: Item) -> None:
        if self.remaining_reload_cooldown > 0:
            return

        if ammo.quantity <= 0 or self.quantity == self.magazine_size:
            return

        # if we have more ammo, reload as much as possible
        total_ammo = self.quantity + ammo.quantity

        if total_ammo <= self.magazine_size:
            ammo.quantity = 0
            self.quantity_after_reload = total_ammo
        else:
            ammo.quantity -= self.magazine_size - self.quantity
            self.quantity_after_reload = self.magazine_size
        self.reload()

    def shoot(self, ammo: Item):
        self.interaction_in_progress = True
        self.quantity -= 1
        self.remaining_shoot_cooldown = self.shoot_cooldown
        self.spawn_bullet()
        self.start_shoot_animation()
        # TODO play shooting sound
        if self.quantity == 0:
            self.handle_reloading(ammo)

    def reload(self) -> None:
        self.interaction_in_progress = True
        self.remaining_reload_cooldown = self.reload_cooldown
        # TODO start reloading animation
        # TODO play reloading sound

    def calculate_initial_bullet_position(self):
        # calculate the position of the barrel end relative to the pivot point
        relative_barrel_end_pos = self.barrel_end_pos - self.pivot

        # calculate the rotation angle in radians
        rotation_rad = math.radians(-self.entity.rot)

        # rotate the relative barrel end position by the gun's rotation
        rotated_relative_barrel_end_pos = pygame.Vector2(
            relative_barrel_end_pos.x * math.cos(rotation_rad) - relative_barrel_end_pos.y * math.sin(rotation_rad),
            relative_barrel_end_pos.x * math.sin(rotation_rad) + relative_barrel_end_pos.y * math.cos(rotation_rad)
        )

        # calculate the position of the barrel end in the world coordinates
        world_barrel_end_pos = rotated_relative_barrel_end_pos + self.pivot

        # calculate the position where the ammo spawns
        pos_x = self.x + world_barrel_end_pos.x
        pos_y = self.y + world_barrel_end_pos.y
        # rotated_offset = self.offset.rotate(-self.entity.rot)  # different weapon animation relative to the player (Ctrl+F: DWARP1)
        # pos_x = self.entity.x + world_barrel_end_pos.x + rotated_offset.x
        # pos_y = self.entity.y + world_barrel_end_pos.y + rotated_offset.y
        position = pygame.Vector2(pos_x, pos_y)
        return position

    def spawn_bullet(self):
        bullet = self.ammo_class(config=self.config, item_name=self.ammo_name, item_type=ItemType.AMMO,
                                 damage=self.damage, spawn_position=self.calculate_initial_bullet_position(),
                                 speed=self.ammo_speed, angle=self.entity.rot)
        self.shot_bullets.add(bullet)

    def set_recoil(self, distance: int, duration: int) -> None:
        self.recoil_distance = distance
        self.recoil_duration = duration
        self.recoil_remaining_duration = 0
        self.recoil_speed = self.recoil_distance / self.recoil_duration
        self.animation_offset = pygame.Vector2(0, 0)

        if self.recoil_duration > self.shoot_cooldown:
            raise Exception("Recoil duration should NOT be greater than shoot cooldown!")

    def start_shoot_animation(self) -> None:
        if self.recoil_remaining_duration > 0:
            return
        self.recoil_remaining_duration = self.recoil_duration
        self.animation_offset = pygame.Vector2(0, 0)

    def shoot_animation(self):
        if self.recoil_remaining_duration == 0:
            return

        half_duration = self.recoil_duration / 2
        recoil_offset = self.recoil_speed * (half_duration - abs(half_duration - self.recoil_remaining_duration + 1)) * 2

        rotation_rad = math.radians(-self.entity.rot)
        self.animation_offset.x = -recoil_offset * math.cos(rotation_rad)
        self.animation_offset.y = -recoil_offset * math.sin(rotation_rad)

        self.recoil_remaining_duration -= 1

        if self.recoil_remaining_duration == 0:
            self.animation_offset = pygame.Vector2(0, 0)
