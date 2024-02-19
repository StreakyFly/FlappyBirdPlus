from typing import Optional
import math

import pygame

from ...item import Item


# TODO Simple collision animation/explosion when colliding with objects.


class Bullet(Item):
    BACKGROUND_VELOCITY = pygame.Vector2(-7.5, 0)

    def __init__(self, spawn_position: pygame.Vector2 = pygame.Vector2(0, 0), damage: int = 0,
                 speed: float = 0, angle: float = 0, *args, **kwargs):
        self.real = not (damage == speed == angle == 0 and spawn_position == pygame.Vector2(0, 0))
        super().__init__(*args, **kwargs)

        self.damage = damage
        self.speed = speed
        self.angle = angle
        self.spawn_position = spawn_position

        # for unique bullets call set_spawn_position() in subclass
        self.set_spawn_position(bullet_offset=pygame.Vector2(-self.w, -self.h / 2))
        # for unique bullets set bullet_front_length in subclass
        self.bullet_front_length = 4  # the length/height of the bullet's front-most part (the part that hits first)

        self.original_image_dimensions = self.image.get_width(), self.image.get_height()
        self.velocity = self.calculate_velocity()
        self.update_image(pygame.transform.rotate(self.image, angle))

        self.pipes = []
        self.enemies = []
        self.player = None
        self.hit_entity: Optional[str] = None  # the entity the bullet hit
        self.previous_front_pos = self.calculate_bullet_front_position()
        self.bounced: bool = False
        self.stopped: bool = False

        self.frame = 0
        self.pipe_to_ignore = None
        self.intersections = dict()

    def tick(self) -> None:
        if not self.real:  # so the inventory slot's bullet doesn't update for no reason
            return

        super().tick()
        self.handle_collision()

        self.previous_front_pos = self.calculate_bullet_front_position()
        self.x += self.velocity.x
        self.y += self.velocity.y

        self.frame += 1

    def draw(self) -> None:
        self.config.screen.blit(self.image, self.rect)
        # self.debug_draw()

    def debug_draw(self) -> None:
        for pipe in self.pipes:
            pygame.draw.circle(self.config.screen, (255, 211, 0), (pipe.x, pipe.y), 10, width=4)
            pygame.draw.circle(self.config.screen, (255, 211, 0), (pipe.x + pipe.w, pipe.y), 10, width=4)
            pygame.draw.circle(self.config.screen, (255, 211, 0), (pipe.x, pipe.y + pipe.h), 10, width=4)
            pygame.draw.circle(self.config.screen, (255, 211, 0), (pipe.x + pipe.w, pipe.y + pipe.h), 10, width=4)

        pygame.draw.circle(self.config.screen, (200, 0, 100), self.calculate_bullet_front_position(), 7, width=3)

        for is_valid, intersections in self.intersections.items():
            for intersection in intersections:
                color = (0, 100, 200) if is_valid == "valid" else (255, 0, 0)
                intersection.x += self.BACKGROUND_VELOCITY.x
                pygame.draw.circle(self.config.screen, color, intersection, 10, width=4)

        prev_front_pos = self.previous_front_pos + self.BACKGROUND_VELOCITY
        pygame.draw.line(self.config.screen, (255, 0, 0), prev_front_pos, self.calculate_bullet_front_position(), width=3)

    def calculate_velocity(self):
        angle_rad = math.radians(-self.angle)

        vel_x = self.speed * math.cos(angle_rad) + self.BACKGROUND_VELOCITY.x
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
           self.y > self.config.window.height + extra:  # or self.y < -extra: <- this should never happen as the bullet gets stopped when it hits the floor
            return True

        # remove the bullet if it hit the player or any of the enemies
        if self.hit_entity and self.hit_entity in ['player', 'enemy']:
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

        # TODO maybe make the bullets bounce only once every few hits? Like 20% bounce rate?
        # bounce the bullet if it hits a pipe for the first time
        for pipe in self.pipes if not self.bounced else []:
            if not self.collide(pipe):
                continue

            self.hit_entity = 'pipe'
            if self.handle_pipe_collision(pipe):
                return

        # handle hitting enemies
        for enemy in self.enemies:
            if not self.collide(enemy):
                continue
            self.hit_entity = 'enemy'
            enemy.change_life(-self.damage)
            return

        # handle hitting player
        if self.player and self.collide(self.player):
            self.hit_entity = 'player'
            self.player.change_life(-self.damage)
            return

    def stop(self):
        self.stopped = True
        self.velocity = self.BACKGROUND_VELOCITY

    def calculate_bullet_front_position(self) -> pygame.Vector2:
        angle_rad = math.radians(-self.angle)

        # calculate the offsets for the front point when the angle is 0
        offset_x = self.original_image_dimensions[0] / 2
        # offset_y = 0  # no vertical offset since we're starting from the center

        rotated_offset_x = offset_x * math.cos(angle_rad)  # - offset_y * math.sin(angle_rad)  # as offset_y = 0
        rotated_offset_y = offset_x * math.sin(angle_rad)  # + offset_y * math.cos(angle_rad)

        # calculate the absolute position of the front of the bullet
        front_x = self.cx + rotated_offset_x
        front_y = self.cy + rotated_offset_y

        return pygame.Vector2(front_x, front_y)

    def handle_pipe_collision(self, pipe) -> bool:
        if self.pipe_to_ignore == pipe:
            return False
        if self.frame < 2:
            self.pipe_to_ignore = pipe
            return False

        TOLERANCE = 5
        # check if the bullet hit any of the pipe's corners
        if (self.previous_front_pos.y < pipe.y + TOLERANCE or self.previous_front_pos.y > pipe.y + pipe.h - TOLERANCE) and \
           (self.previous_front_pos.x < pipe.x + TOLERANCE or self.previous_front_pos.x > pipe.x + pipe.w - TOLERANCE) and \
           self.is_pipe_corner_hit(pipe):
            self.bounce(True, True)
            return True

        bfp = self.calculate_bullet_front_position()

        # calculate intersection points with each side of the pipe
        intersection_left = pygame.Vector2(pipe.x, bfp.y + self.velocity.y * ((pipe.x - bfp.x) / self.velocity.x))
        intersection_right = pygame.Vector2(pipe.x + pipe.w, bfp.y + self.velocity.y * ((pipe.x + pipe.w - bfp.x) / self.velocity.x))
        intersection_top = pygame.Vector2(bfp.x + self.velocity.x * ((pipe.y - bfp.y) / self.velocity.y), pipe.y)
        intersection_bottom = pygame.Vector2(bfp.x + self.velocity.x * ((pipe.y + pipe.h - bfp.y) / self.velocity.y), pipe.y + pipe.h)

        valid_intersections = []
        # intersection is valid if its x or y lies on the pipe's side
        if pipe.y <= intersection_left.y <= pipe.y + pipe.h:
            valid_intersections.append(intersection_left)
        if pipe.y <= intersection_right.y <= pipe.y + pipe.h:
            valid_intersections.append(intersection_right)
        if pipe.x <= intersection_top.x <= pipe.x + pipe.w:
            valid_intersections.append(intersection_top)
        if pipe.x <= intersection_bottom.x <= pipe.x + pipe.w:
            valid_intersections.append(intersection_bottom)

        invalid_intersections = [i for i in [intersection_left, intersection_right, intersection_top, intersection_bottom] if i not in valid_intersections]
        self.intersections = {"valid": valid_intersections, "invalid": invalid_intersections}  # for debugging only

        closest = None
        if valid_intersections:
            closest = min(valid_intersections, key=lambda intersection: (intersection - self.previous_front_pos).length_squared())

        if closest in [intersection_left, intersection_right]:
            self.bounce(True, False)
        elif closest in [intersection_top, intersection_bottom]:
            self.bounce(False, True)

        return True

    def bounce(self, x: bool, y: bool) -> None:
        self.bounced = True
        self.velocity *= 0.9  # reduce the bullet's speed after bouncing

        if x:
            self.velocity.x = -self.velocity.x + self.BACKGROUND_VELOCITY.x * 2
            self.angle = (180 - self.angle) % 360
            self.update_image(pygame.transform.flip(self.image, True, False))
        if y:
            self.velocity.y = -self.velocity.y
            self.angle = -self.angle
            self.update_image(pygame.transform.flip(self.image, False, True))

    def is_pipe_corner_hit(self, pipe, tolerance=3.0) -> bool:
        # figure out which corner of the pipe was possibly hit
        pipe_corner: pygame.Vector2 = pygame.Vector2(pipe.x, pipe.y + pipe.h)

        # bottom left corner
        if self.previous_front_pos.y > pipe.y + pipe.h - tolerance and self.previous_front_pos.x < pipe.x + tolerance:
            pipe_corner = pygame.Vector2(pipe.x, pipe.y + pipe.h)
        # top left corner
        elif self.previous_front_pos.y < pipe.y + tolerance and self.previous_front_pos.x < pipe.x + tolerance:
            pipe_corner = pygame.Vector2(pipe.x, pipe.y)
        # bottom right corner
        elif self.previous_front_pos.y > pipe.y + pipe.h - tolerance and self.previous_front_pos.x > pipe.x + pipe.w - tolerance:
            pipe_corner = pygame.Vector2(pipe.x + pipe.w, pipe.y + pipe.h)
        # top right corner
        elif self.previous_front_pos.y < pipe.y + tolerance and self.previous_front_pos.x > pipe.x + pipe.w - tolerance:
            pipe_corner = pygame.Vector2(pipe.x + pipe.w, pipe.y)

        current_front_pos = self.calculate_bullet_front_position()
        tolerance2 = self.bullet_front_length / 2 + 3  # 3 = margin of error
        return self.is_point_on_line(self.previous_front_pos, current_front_pos, pipe_corner, tolerance2)

    def is_point_on_line(self, p1, p2, p3, tolerance=1.0) -> bool:
        # calculate the coefficients of the line passing through point1 and point2: Ax + By + C = 0
        A = p2.y - p1.y
        B = p1.x - p2.x
        C = p1.y * (p2.x - p1.x) - p1.x * (p2.y - p1.y)

        # calculate the distance of point3 from the line using the formula for distance
        distance = abs(A * p3.x + B * p3.y + C) / ((A ** 2 + B ** 2) ** 0.5)

        return distance <= tolerance
