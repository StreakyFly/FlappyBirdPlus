import pygame
import math

from ...item import Item


class Ammo(Item):
    def __init__(self, damage: int = 0, spawn_position: pygame.Vector2 = pygame.Vector2(0, 0),
                 speed: float = 0, angle: float = 0, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.damage = damage
        self.x = spawn_position.x
        self.y = spawn_position.y
        self.speed = speed
        self.angle = angle
        self.velocity = self.calculate_velocity()
        rotated_image = pygame.transform.rotate(self.config.images.items[self.name.value], angle)
        self.update_image(rotated_image, self.image.get_width(), self.image.get_height())

    def draw(self) -> None:
        self.x += self.velocity.x
        self.y += self.velocity.y
        super().draw()

    def calculate_velocity(self):
        angle_rad = math.radians(-self.angle)

        vel_x = self.speed * math.cos(angle_rad)
        vel_y = self.speed * math.sin(angle_rad)

        return pygame.Vector2(vel_x, vel_y)
