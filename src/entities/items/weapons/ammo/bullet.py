import pygame
import math

from ...item import Item

# TODO should ammo collide with floor and pipes? If yes, there should be a simple collision animation.


class Bullet(Item):
    def __init__(self, spawn_position: pygame.Vector2 = pygame.Vector2(0, 0), damage: int = 0,
                 speed: float = 0, angle: float = 0, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.damage = damage
        self.speed = speed
        self.angle = angle
        self.spawn_position = spawn_position

        # for unique bullets call set_spawn_position() in subclass again
        self.set_spawn_position(bullet_offset=pygame.Vector2(-self.w, -self.h / 2))

        self.velocity = self.calculate_velocity()
        rotated_image = pygame.transform.rotate(self.config.images.items[self.name.value], angle)
        self.update_image(rotated_image, self.image.get_width(), self.image.get_height())

    def draw(self) -> None:
        self.x += self.velocity.x
        self.y += self.velocity.y
        # pygame.draw.circle(self.config.screen, (0, 200, 111), (self.x, self.y), 20, width=8)  # for debugging
        self.config.screen.blit(self.image, self.rect)

    def calculate_velocity(self):
        angle_rad = math.radians(-self.angle)

        vel_x = self.speed * math.cos(angle_rad)
        vel_y = self.speed * math.sin(angle_rad)

        return pygame.Vector2(vel_x, vel_y)

    def set_spawn_position(self, bullet_offset: pygame.Vector2):
        rotated_offset = bullet_offset.rotate(self.angle)
        self.x = self.spawn_position.x + rotated_offset.x
        self.y = self.spawn_position.y - rotated_offset.y

    def stop(self):
        # TODO implement this method
        self.velocity = pygame.Vector2(0, 0)
