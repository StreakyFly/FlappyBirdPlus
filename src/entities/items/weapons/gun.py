import math

import pygame

from ....utils import rotate_on_pivot
from ..item import Item, ItemName, ItemType


class Gun(Item):
    def __init__(self, ammo_name: ItemName, ammo_class: callable, damage: int, ammo_speed: int, magazine_size: int,
                 shoot_cooldown: int, reload_cooldown: int, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ammo_name = ammo_name
        self.ammo_class = ammo_class
        self.damage = damage
        self.ammo_speed = ammo_speed
        self.magazine_size = magazine_size
        self.shoot_cooldown = shoot_cooldown
        self.reload_cooldown = reload_cooldown
        self.remaining_shoot_cooldown = 0
        self.remaining_reload_cooldown = 0
        self.quantity_after_reload = magazine_size
        self.interaction_in_progress: bool = False

        self.offset = pygame.Vector2(0, 0)
        self.pivot_offset = pygame.Vector2(0, 0)
        self.barrel_end_pos = pygame.Vector2(0, 0)
        self.ammo_dimensions = pygame.Vector2(0, 0)

        self.shot_bullets = set()

    def tick(self) -> None:
        if len(self.shot_bullets) > 0:
            self.tick_ammo()
        print(len(self.shot_bullets))
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
            # remove bullets if they are out of the window
            # TODO add some extra space so the bullets don't disappear immediately after they leave the screen
            if bullet.x > self.config.window.width or bullet.y < 0 or bullet.y > self.config.window.height or bullet.x < 0:
                self.shot_bullets.remove(bullet)
                continue
            # TODO remove bullets if they hit enemies (if any enemy is even spawned)
            bullet.tick()

    def draw(self) -> None:
        self.x = self.entity.x + self.offset.x
        self.y = self.entity.y + self.offset.y
        pivot_point = pygame.Vector2(self.entity.x + self.pivot_offset.x, self.entity.y + self.pivot_offset.y)
        origin_point = pygame.Vector2(self.rect.center)
        rotated_image, rotated_rect = rotate_on_pivot(self.image, self.entity.rot, pivot_point, origin_point)
        self.config.screen.blit(rotated_image, rotated_rect)

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
            self.shoot()
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

    def shoot(self):
        # TODO FIRE!
        print("PEW")
        self.interaction_in_progress = True
        self.quantity -= 1
        self.remaining_shoot_cooldown = self.shoot_cooldown
        self.spawn_bullet()

    def reload(self) -> None:
        # TODO RELOAD!
        print("Reloading...")
        self.interaction_in_progress = True
        self.remaining_reload_cooldown = self.reload_cooldown

    def calculate_initial_bullet_position(self):
        # calculate the position of the barrel end relative to the pivot point
        relative_barrel_end_pos = self.barrel_end_pos - self.pivot_offset

        # calculate the rotation angle in radians
        rotation_rad = math.radians(-self.calculate_rotation())

        # rotate the relative barrel end position by the gun's rotation
        rotated_relative_barrel_end_pos = pygame.Vector2(
            relative_barrel_end_pos.x * math.cos(rotation_rad) - relative_barrel_end_pos.y * math.sin(rotation_rad),
            relative_barrel_end_pos.x * math.sin(rotation_rad) + relative_barrel_end_pos.y * math.cos(rotation_rad)
        )

        # calculate the position of the barrel end in the world coordinates
        world_barrel_end_pos = rotated_relative_barrel_end_pos + self.pivot_offset

        # calculate the position where the ammo spawns
        pos_x = self.x + world_barrel_end_pos.x - self.ammo_dimensions.x
        pos_y = self.y + world_barrel_end_pos.y - self.ammo_dimensions.y / 2
        position = pygame.Vector2(pos_x, pos_y)
        return position

    def calculate_angle(self, vector1, vector2):
        dot_product = vector1.dot(vector2)
        magnitude_product = vector1.magnitude() * vector2.magnitude()
        value = pygame.math.clamp(dot_product / magnitude_product, -1.0, 1.0)
        angle_rad = math.acos(value)
        angle_deg = math.degrees(angle_rad)

        cross_product = vector1.x * vector2.y - vector1.y * vector2.x
        if cross_product > 0:
            angle_deg = -angle_deg

        return angle_deg

    def calculate_rotation(self):
        # rotation = self.entity.rot might work fine? Or maybe not in cases where pivot is not in the middle of the gun.
        pivot_point = pygame.Vector2(self.entity.x + self.pivot_offset.x, self.entity.y + self.pivot_offset.y)
        origin_point = pygame.Vector2(self.rect.center)
        _, rotated_rect = rotate_on_pivot(self.image, self.entity.rot, pivot_point, origin_point)

        new_position = pygame.Vector2(rotated_rect.center)
        vector1 = origin_point - pivot_point
        vector2 = new_position - pivot_point
        rotation = self.calculate_angle(vector1, vector2)
        return rotation

    def spawn_bullet(self):
        bullet = self.ammo_class(config=self.config, item_name=self.ammo_name, item_type=ItemType.AMMO,
                                 damage=self.damage, spawn_position=self.calculate_initial_bullet_position(),
                                 speed=self.ammo_speed, angle=self.calculate_rotation())
        self.shot_bullets.add(bullet)
