import math

import pygame

from ....utils import rotate_on_pivot, printc
from ..item import Item, ItemName, ItemType

"""
The recoil animation currently does not work well with fast-firing guns, eg. Uzi, where self.recoil_duration is greater
than self.shoot_cooldown (self.recoil_duration > self.shoot_cooldown).
This is because the gun can fire again before the recoil animation from the previous shot has completed, leading to the
animation being reset with each new shot. Instead of resetting, the animation should incorporate the new recoil force
into the existing one, allowing the recoil effects to accumulate. Consequently, with continuous firing, the gun would
be pushed back and up incrementally, reflecting a more realistic behavior.
"""


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
        self.ammo_item = None  # ammo item from the inventory slot[1]

        self.remaining_shoot_cooldown = 0
        self.remaining_reload_cooldown = 0
        self.quantity_after_reload = 0
        self.interaction_in_progress: bool = False
        self.rotation = 0

        self.offset = pygame.Vector2(0, 0)
        self.pivot = pygame.Vector2(0, 0)
        self.barrel_end_pos = pygame.Vector2(0, 0)

        self.recoil_distance = 15
        self.recoil_duration = 6
        self.recoil_rotation = 10
        self.remaining_recoil_duration = 0
        self.recoil_speed = self.recoil_distance / self.recoil_duration
        self.animation_offset = pygame.Vector2(0, 0)
        self.animation_rotation = 0

        self.update_transform()

        self.shot_bullets = set()

    def tick(self) -> None:
        self.update_transform()
        self.shoot_animation()
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

        if self.remaining_cooldown > 0:
            self.remaining_cooldown -= 1

    def tick_ammo(self) -> None:
        for bullet in set(self.shot_bullets):
            bullet.tick()
            if bullet.should_remove():
                self.shot_bullets.remove(bullet)

    def flip(self) -> None:
        super().flip()
        self.pivot = pygame.Vector2(self.w - self.pivot.x, self.pivot.y)
        self.barrel_end_pos = pygame.Vector2(self.w - self.barrel_end_pos.x, self.barrel_end_pos.y)
        self.set_recoil(-self.recoil_distance, self.recoil_duration, -self.recoil_rotation)

    def draw(self) -> None:
        pivot_point = pygame.Vector2(self.x + self.pivot.x, self.y + self.pivot.y)
        rotated_image, rotated_rect = rotate_on_pivot(self.image, self.rotation, pivot_point, self.rect.center)
        self.config.screen.blit(rotated_image, rotated_rect)
        # self.debug_draw()

    def debug_draw(self) -> None:
        RED = (255, 0, 0); GREEN = (0, 255, 0); BLUE = (0, 0, 255); BLACK = (0, 0, 0)
        screen = self.config.screen
        pygame.draw.circle(screen, RED, self.calculate_initial_bullet_position(), 8, width=4)
        pygame.draw.circle(screen, BLACK, (self.x + self.barrel_end_pos.x, self.y + self.barrel_end_pos.y), 6, width=3)
        pygame.draw.circle(screen, RED, (self.x + self.pivot.x, self.y + self.pivot.y), 4)

    def stop(self) -> None:
        for bullet in self.shot_bullets:
            bullet.stop()

    def update_transform(self) -> None:
        self.x = self.entity.x + self.offset.x + self.animation_offset.x
        self.y = self.entity.y + self.offset.y + self.animation_offset.y
        self.rotation = self.entity.rotation + self.animation_rotation

    def update_ammo_object(self, ammo_item: Item) -> None:
        self.ammo_item = ammo_item

    def set_positions(self, offset: pygame.Vector2, pivot: pygame.Vector2, barrel_end_pos: pygame.Vector2) -> None:
        self.offset = offset
        self.pivot = pivot
        self.barrel_end_pos = barrel_end_pos
        self.update_transform()

    def update_offset(self, offset) -> None:
        self.offset = pygame.Vector2(offset)

    def set_properties(self, ammo_name: ItemName, ammo_class: callable, damage: int, ammo_speed: int, magazine_size: int,
                       shoot_cooldown: int, reload_cooldown: int) -> None:
        self.ammo_name = ammo_name
        self.ammo_class = ammo_class
        self.damage = damage
        self.ammo_speed = ammo_speed
        self.magazine_size = magazine_size
        self.shoot_cooldown = shoot_cooldown
        self.reload_cooldown = reload_cooldown
        self.quantity_after_reload = magazine_size

    def use(self, action, *args) -> None:
        if action == 0:
            self.handle_shooting()
            return
        elif action == 1:
            self.handle_reloading()
            return

    def handle_shooting(self) -> None:
        if self.interaction_in_progress:
            return

        # if weapon magazine isn't empty, shoot
        if self.quantity > 0:
            self.shoot()
            return

        # if gun is empty, try reloading it
        self.handle_reloading()

    def handle_reloading(self) -> None:
        if self.remaining_reload_cooldown > 0:
            return

        if self.ammo_item.quantity <= 0 or self.quantity == self.magazine_size:
            return

        # if we have more ammo, reload as much as possible
        total_ammo = self.quantity + self.ammo_item.quantity

        if total_ammo <= self.magazine_size:
            self.ammo_item.quantity = 0
            self.quantity_after_reload = total_ammo
        else:
            self.ammo_item.quantity -= self.magazine_size - self.quantity
            self.quantity_after_reload = self.magazine_size
        self.reload()

    def shoot(self) -> None:
        self.interaction_in_progress = True
        self.quantity -= 1
        self.remaining_shoot_cooldown = self.shoot_cooldown
        self.set_cooldown(self.shoot_cooldown)
        self.spawn_bullet()
        self.start_shoot_animation()
        # TODO play shooting sound

        if self.quantity == 0:
            self.handle_reloading()

    def reload(self) -> None:
        self.interaction_in_progress = True
        self.remaining_reload_cooldown = self.reload_cooldown
        self.set_cooldown(self.reload_cooldown)
        # TODO start reloading animation
        # TODO play reloading sound

    def calculate_initial_bullet_position(self) -> pygame.Vector2:
        # calculate the position of the barrel end relative to the pivot point
        relative_barrel_end_pos = self.barrel_end_pos - self.pivot

        # calculate the rotation angle in radians
        rotation_rad = math.radians(-self.rotation)

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
        return pygame.Vector2(pos_x, pos_y)

    def spawn_bullet(self) -> None:
        bullet = self.ammo_class(config=self.config, item_name=self.ammo_name, item_type=ItemType.AMMO,
                                 damage=self.damage, spawn_position=self.calculate_initial_bullet_position(),
                                 speed=self.ammo_speed, angle=self.rotation)
        bullet.entity = self.entity
        if self.flipped:
            bullet.flip()
        self.shot_bullets.add(bullet)

    def set_recoil(self, distance: int, duration: int, rotation: int) -> None:
        self.recoil_distance = distance
        self.recoil_duration = duration
        self.recoil_rotation = rotation
        self.remaining_recoil_duration = 0
        self.recoil_speed = self.recoil_distance / self.recoil_duration
        self.animation_offset = pygame.Vector2(0, 0)
        self.animation_rotation = 0

        if self.recoil_duration > self.shoot_cooldown:
            printc(f"WARNING: '{self.name}' - recoil duration is greater than shoot cooldown!", color="yellow")

    def start_shoot_animation(self) -> None:
        # if self.remaining_recoil_duration > 0:
        #     return
        self.remaining_recoil_duration = self.recoil_duration
        self.animation_offset = pygame.Vector2(0, 0)
        self.animation_rotation = 0

    def shoot_animation(self) -> None:
        if self.remaining_recoil_duration == 0:
            return

        half_duration = self.recoil_duration / 2
        recoil_progress = abs(1 - abs(half_duration - self.remaining_recoil_duration + 1) / half_duration)
        recoil_offset = self.recoil_speed * (half_duration - abs(half_duration - self.remaining_recoil_duration + 1)) * 2

        rotation_rad = math.radians(-self.entity.rotation)
        self.animation_offset.x = -recoil_offset * math.cos(rotation_rad)
        self.animation_offset.y = -recoil_offset * math.sin(rotation_rad)

        self.animation_rotation = self.recoil_rotation * recoil_progress

        self.remaining_recoil_duration -= 1

        if self.remaining_recoil_duration == 0:
            self.animation_offset = pygame.Vector2(0, 0)
            self.animation_rotation = 0
