from typing import Optional
import math

import pygame

from ...item import Item

# TODO Simple collision animation/explosion when colliding with objects.


class Bullet(Item):
    def __init__(self, spawn_position: pygame.Vector2 = pygame.Vector2(0, 0), damage: int = 0,
                 speed: float = 0, angle: float = 0, *args, **kwargs):
        self.real = not (damage == speed == angle == 0 and spawn_position == pygame.Vector2(0, 0))
        super().__init__(*args, **kwargs)

        self.damage = damage
        self.speed = speed
        self.angle = angle
        self.spawn_position = spawn_position

        self.hit_entity: Optional[str] = None  # the entity the bullet hit

        # for unique bullets call set_spawn_position() in subclass again
        self.set_spawn_position(bullet_offset=pygame.Vector2(-self.w, -self.h / 2))

        self.velocity = self.calculate_velocity()
        rotated_image = pygame.transform.rotate(self.image, angle)
        self.update_image(rotated_image)

        self.pipes = None
        self.enemies = None
        self.player = None
        self.previous_position = pygame.Vector2(self.x, self.y)
        self.bounced: bool = False
        self.stopped: bool = False

    def tick(self) -> None:
        if not self.real:  # so the inventory slot's bullet doesn't update for no reason
            return

        self.handle_collision()
        super().tick()

        self.previous_position = pygame.Vector2(self.x, self.y)
        self.x += self.velocity.x
        self.y += self.velocity.y

    def draw(self) -> None:
        # pygame.draw.circle(self.config.screen, (50, 240, 0), (self.x, self.y), 20, width=4)  # for debugging
        self.config.screen.blit(self.image, self.rect)

    def calculate_velocity(self):
        angle_rad = math.radians(-self.angle)

        vel_x = self.speed * math.cos(angle_rad) - 7.5  # background_velocity.x = -7.5
        vel_y = self.speed * math.sin(angle_rad)

        return pygame.Vector2(vel_x, vel_y)

    def set_spawn_position(self, bullet_offset: pygame.Vector2):
        rotated_offset = bullet_offset.rotate(self.angle)
        self.x = self.spawn_position.x + rotated_offset.x
        self.y = self.spawn_position.y - rotated_offset.y

    def set_entities(self, player, enemies, pipes):
        self.player = player
        self.enemies = enemies
        self.pipes = pipes

    def should_remove(self) -> bool:
        # remove the bullet if it's out of the game window
        extra = self.config.window.height * 0.2
        if self.x > self.config.window.width + 2 * extra or self.x < -extra or \
                self.y > self.config.window.height + extra:  # or bullet.y < -extra:
            return True

        if not self.hit_entity:
            return False

        # remove the bullet if it hit the player or enemy
        if self.hit_entity in ['player', 'enemy']:
            return True

        return False

    def handle_collision(self) -> None:
        if self.stopped:
            return

        # stop the bullet if it hits the floor
        if self.y > self.config.window.height - 163 - self.h / 2:
            self.hit_entity = 'floor'
            self.stop()
            return

        # bounce the bullet if it hits a pipe
        if self.pipes:
            for pipe in self.pipes.upper + self.pipes.lower:
                if self.bounced:  # if the bullet already bounced, don't bounce again
                    continue

                if not self.collide(pipe):
                    continue

                self.hit_entity = 'pipe'

                # TODO improve this - both if statements are true way too often, but they should only be if pipe's
                #  corner is hit. Maybe check how far from the pipe's corner the front of the bullet is, also
                #  including the bullet's rotation.
                # TODO and maybe make bullets bounce only once every few hits? Like 20% bounce rate?
                if self.previous_position.y < pipe.y or self.previous_position.y > pipe.y + pipe.h:
                    self.velocity.y = -self.velocity.y
                    self.update_image(pygame.transform.flip(self.image, False, True))
                if self.previous_position.x < pipe.x or self.previous_position.x > pipe.x + pipe.w:
                    self.velocity.x = -self.velocity.x
                    vel_x, _ = self.calculate_velocity()
                    self.velocity.x = vel_x if self.velocity.x > 0 else -vel_x - 7.5 * 2
                    self.update_image(pygame.transform.flip(self.image, True, False))

                self.velocity *= 0.9  # reduce the bullet's speed after bouncing
                self.bounced = True
                return

        # handle hitting enemies
        if self.enemies:
            for enemy in self.enemies:
                if self.collide(enemy):
                    self.hit_entity = 'enemy'
                    enemy.change_life(-self.damage)
                    return

        # handle hitting player
        if self.player:
            if self.collide(self.player):
                self.hit_entity = 'player'
                self.player.change_life(-self.damage)
                return

    def stop(self):
        self.stopped = True
        self.velocity = pygame.Vector2(-7.5, 0)
