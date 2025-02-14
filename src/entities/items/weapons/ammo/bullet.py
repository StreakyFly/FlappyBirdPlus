import math
from typing import Callable, Union, Optional

import pygame

from ...item import Item


# TODO Simple collision animation/explosion when colliding with objects.

"""
Special bullet velocity calculations
====================================
Brief explanation:
  The x velocity of the entity that fired the gun is only partially considered, while its y velocity
  is completely disregarded, as it doesn't suit the game's visual style.
  
Some interesting videos on the topic, for better understanding:
    - https://www.youtube.com/watch?v=eQwVjREMp5s
    - https://www.youtube.com/watch?v=436i_cTdtVo
    - https://www.youtube.com/watch?v=ZH7GpYJoptU   

Key considerations:
  The entity's y velocity when firing the gun is not taken into account for two reasons:
   1. to simplify both code and gameplay
   2. it looks weird, as the player's y velocity is very volatile, making the bullet's path too hard to predict

  The entity's x velocity when firing the gun is taken into account, but only partially, for two reasons:
   1. ignoring the x velocity entirely looks out of place (unlike with y velocity)
   2. since the y velocity isn't considered, incorporating the full x velocity seems weird, so we only account for half

Detailed explanation with examples and formulas:
  Player's x velocity in the game world is 7.5 but visually, on the screen (relative to the camera), it's 0.
  Other entities, like enemies (Cloudskimmer), have the same x velocity as the player once they get into position.
  We'll neglect the x velocity prior to getting in position (for example Cloudskimmer's initial velocity).
    
  Here are the numbers we'll use for example calculations:
    (REAL velocity: how much the object moves in the game world)
    (VISUAL velocity: relative to the camera - how much the object moves on the screen)
   RAW_BULLET_VELOCITY is set for each gun, while other velocities are constants.
   RAW_BULLET_VELOCITY = (15, 0)  # at what velocity does the gun fire the bullet (other velocities aren't included)
   REAL_ENTITY_VELOCITY = (7.5, 0)  # how much the entity that fired the gun moves in the game world
   REAL_CAMERA_VELOCITY = (7.5, 0)  # how much the camera moves in the game world
   VISUAL_BACKGROUND_VELOCITY = (-7.5, 0)  # how much the background moves on the screen
   Moreover, REAL_ENTITY_VELOCITY.x = REAL_CAMERA_VELOCITY.x = -VISUAL_BACKGROUND_VELOCITY.x = 7.5
    
  Whether the bullet is flying to the right or left, it's always "gliding" with half of VISUAL_BACKGROUND_VELOCITY.x.

  Imagine you're looking through a camera. The camera is linked with the player's X axis (horizontally).
  When the player moves to the right, the camera moves to the right as well,
  so visually the player stays still, while the background moves to the left.

  So, if the entity (& camera) moves to the right and the bullet moves to either left/right, what will its x velocity be?
   If the camera moves to the right, and the bullet moves to the right, the bullet visually (relative to the camera)
     moves to the right less than it would if the camera were stationary.
   If the camera moves to the right, and the bullet moves to the left, the bullet visually (relative to the camera)
     moves to the left more than it would if the camera were stationary

   Keep in mind for these examples we'll use full entity's x velocity, not half of it, so it's easier to understand.
    1. BEFORE bouncing; bullet moves to the Right; RAW_BULLET_VELOCITY = (15, 0)
     How fast does the bullet move in the game world?
      REAL_BULLET_VELOCITY.x = RAW_BULLET_VELOCITY.x + REAL_ENTITY_VELOCITY.x
      REAL_BULLET_VELOCITY.x = 15 + 7.5 = 22.5
     How fast does the bullet move on the screen?
      VISUAL_BULLET_VELOCITY.x = RAW_BULLET_VELOCITY.x + REAL_ENTITY_VELOCITY.x - REAL_CAMERA_VELOCITY.x
      VISUAL_BULLET_VELOCITY.x = RAW_BULLET_VELOCITY.x  # as REAL_ENTITY_VELOCITY.x == REAL_CAMERA_VELOCITY.x, so they cancel out
      VISUAL_BULLET_VELOCITY.x = 15

    2. BEFORE bouncing; bullet moves to the Left; RAW_BULLET_VELOCITY = (-15, 0)
     How fast does the bullet move in the game world?
      REAL_BULLET_VELOCITY.x = RAW_BULLET_VELOCITY.x + REAL_ENTITY_VELOCITY.x
      REAL_BULLET_VELOCITY.x = -15 + 7.5 = -7.5
     How fast does the bullet move on the screen?
      VISUAL_BULLET_VELOCITY.x = RAW_BULLET_VELOCITY.x + REAL_ENTITY_VELOCITY.x - REAL_CAMERA_VELOCITY.x
      VISUAL_BULLET_VELOCITY.x = RAW_BULLET_VELOCITY.x  # as REAL_ENTITY_VELOCITY.x == REAL_CAMERA_VELOCITY.x, so they cancel out
      VISUAL_BULLET_VELOCITY.x = -15
    
    3. AFTER bouncing; bullet moves to the Left; RAW_BULLET_VELOCITY = (15, 0)
     How fast does the bullet move in the game world?
      REAL_BULLET_VELOCITY.x = -(RAW_BULLET_VELOCITY.x + REAL_ENTITY_VELOCITY.x)
      REAL_BULLET_VELOCITY.x = -(15 + 7.5) = -22.5
     How fast does the bullet move on the screen?
      VISUAL_BULLET_VELOCITY.x = -(RAW_BULLET_VELOCITY.x + REAL_ENTITY_VELOCITY.x + REAL_CAMERA_VELOCITY.x)
      VISUAL_BULLET_VELOCITY.x = -(15 + 7.5 + 7.5) = -30

    4. AFTER bouncing; bullet moves to the Right; RAW_BULLET_VELOCITY = (-15, 0)
     How fast does the bullet move in the game world?
      REAL_BULLET_VELOCITY.x = -(RAW_BULLET_VELOCITY.x + REAL_ENTITY_VELOCITY.x)
      REAL_BULLET_VELOCITY.x = -(-15 + 7.5) = -(-7.5) = 7.5
     How fast does the bullet move on the screen?
      VISUAL_BULLET_VELOCITY.x = -(RAW_BULLET_VELOCITY.x + REAL_ENTITY_VELOCITY.x + REAL_CAMERA_VELOCITY.x)
      VISUAL_BULLET_VELOCITY.x = -(-15 + 7.5 + 7.5) = -(0) = 0  # it is 0 by coincidence, it is not always 0
"""


class Bullet(Item):
    VISUAL_BACKGROUND_VELOCITY = pygame.Vector2(-7.5, 0)  # how much the background moves on the screen
    REAL_CAMERA_VELOCITY = pygame.Vector2(7.5, 0)  # how much the camera moves in the game world

    def __init__(self, spawn_position: pygame.Vector2 = pygame.Vector2(0, 0), damage: int = 0,
                 speed: float = 0, angle: float = 0, flipped: bool = False,
                 spawn_pos_offset: Optional[Union[pygame.Vector2, Callable[['Bullet'], pygame.Vector2]]] = None,
                 *args, **kwargs):
        self.real = not (damage == speed == angle == 0 and spawn_position == pygame.Vector2(0, 0))
        super().__init__(*args, **kwargs)

        self.damage = damage
        self.speed = speed
        self.angle = angle
        self.spawn_position = spawn_position

        self.original_image = self.image
        self.original_image_dimensions = pygame.Vector2(self.image.get_width(), self.image.get_height())
        self.velocity = self.calculate_velocity()
        self.update_image(pygame.transform.rotate(self.image, angle))

        self.bounced: bool = False
        self.stopped: bool = False
        self.pipes = []
        self.enemies = []
        self.player = None
        self.hit_entity: Optional[str] = None  # the entity the bullet hit
        self.frame: int = 0
        self.pipe_to_ignore = None

        if self.config.debug:
            self.intersections = {"valid": [], "invalid": []}

        # for unique bullets set bullet_front_length in subclass
        self.bullet_front_length = 4  # the length/height of the bullet's front-most part (the part that hits first)

        # Must be set after updating the image, so callable can access image dimensions, like self.w, if necessary.
        # Subclass usage: super().__init__(spawn_pos_offset=lambda x: pygame.Vector2(-self.w * 0.4, 0), *args, **kwargs)
        if spawn_pos_offset:
            self.spawn_pos_offset = spawn_pos_offset(self) if callable(spawn_pos_offset) else spawn_pos_offset
        else:
            self.spawn_pos_offset = pygame.Vector2(self.w * 0.4, 0)

        if flipped:
            self.flip()

        self.set_spawn_position()

        self.prev_front_pos: pygame.Vector2 = self.calculate_bullet_front_position()
        self.curr_front_pos: pygame.Vector2 = self.prev_front_pos

    def flip(self):
        self.update_image(self.original_image)
        super().flip()
        self.original_image = self.image
        self.update_image(pygame.transform.rotate(self.original_image, self.angle))
        self.speed = -self.speed
        self.velocity = self.calculate_velocity()
        self.spawn_pos_offset.x = -self.spawn_pos_offset.x

    def tick(self) -> None:
        if not self.real:  # so the inventory slot's bullet doesn't update for no reason
            return

        self.prev_front_pos = self.curr_front_pos
        self.x += self.velocity.x
        self.y += self.velocity.y

        self.handle_collision()

        self.curr_front_pos = self.calculate_bullet_front_position()

        self.frame += 1
        super().tick()

    def draw(self) -> None:
        self.config.screen.blit(self.image, self.rect)

    def debug_draw(self) -> None:
        # rename big-bullet_debug.png to big-bullet.png to see the debug drawing
        screen = self.config.screen
        for pipe in self.pipes:
            pygame.draw.circle(screen, (255, 211, 0), (pipe.x, pipe.y), 10, width=4)
            pygame.draw.circle(screen, (255, 211, 0), (pipe.x + pipe.w, pipe.y), 10, width=4)
            pygame.draw.circle(screen, (255, 211, 0), (pipe.x, pipe.y + pipe.h), 10, width=4)
            pygame.draw.circle(screen, (255, 211, 0), (pipe.x + pipe.w, pipe.y + pipe.h), 10, width=4)

        pygame.draw.circle(screen, (200, 0, 100), self.curr_front_pos, 7, width=3)
        pygame.draw.circle(screen, (0, 25, 255), self.curr_front_pos, 14, width=8)
        pygame.draw.circle(screen, (0, 255, 55), self.spawn_position, 9, width=6)

        for is_valid, intersections in self.intersections.items():
            for intersection in intersections:
                color = (0, 100, 200) if is_valid == "valid" else (255, 0, 0)
                pygame.draw.circle(screen, color, intersection, 10, width=4)
                intersection.x += self.VISUAL_BACKGROUND_VELOCITY.x if self.velocity != pygame.Vector2(0, 0) else 0

        prev_front_pos_real = self.prev_front_pos - self.REAL_CAMERA_VELOCITY * 0.5  # how much the bullet moved in the game world
        prev_front_pos_visual = self.prev_front_pos  # how much the bullet moved on the screen
        pygame.draw.line(screen, (0, 255, 0), prev_front_pos_real, self.curr_front_pos, width=3)
        pygame.draw.line(screen, (255, 0, 0), prev_front_pos_visual, self.curr_front_pos, width=3)
        super().debug_draw()

    def calculate_velocity(self):
        angle_rad = math.radians(-self.angle)

        # More realistic, as entity's x velocity is taken into account (considering entity is visually static on screen,
        # like the player or CloudSkimmer enemy (once it gets into position)).
        # How is it taken into account if we don't add anything else, other than the bullet's x velocity? The background
        # is visually moving to the left at the speed of player's x velocity, so we don't have to add anything.
        # However, this "realism" looks a bit weird as entity's y velocity is not taken into account, and because the
        # bullets travel at such slow speeds in this game. That's why I decided not to use this formula.
        # vel_x = self.speed * math.cos(angle_rad)  # <-- bullet's x velocity

        # Less realistic, as only half of entity's x velocity is taken into account, but it fits the style a bit better.
        # Subtracting REAL_CAMERA_VELOCITY.x * 1 would take into account full camera movement, which would entirely
        # cancel out the entity's x velocity, but we're only taking half of it into account.
        vel_x = self.speed * math.cos(angle_rad) - self.REAL_CAMERA_VELOCITY.x * 0.5

        # Camera/background is not moving vertically, so entity's y velocity is not taken into account,
        # neither visually on screen nor in game world.
        vel_y = self.speed * math.sin(angle_rad)

        return pygame.Vector2(vel_x, vel_y)

    def set_spawn_position(self):
        front_pos_offset = self.calculate_bullet_front_position()
        offset_x = self.spawn_position.x - front_pos_offset.x
        offset_y = self.spawn_position.y - front_pos_offset.y

        if self.spawn_pos_offset:
            angle_rad = math.radians(-self.angle)
            rotated_offset = pygame.Vector2(
                self.spawn_pos_offset.x * math.cos(angle_rad) - self.spawn_pos_offset.y * math.sin(angle_rad),
                self.spawn_pos_offset.x * math.sin(angle_rad) + self.spawn_pos_offset.y * math.cos(angle_rad)
            )
            offset_x += rotated_offset.x
            offset_y += rotated_offset.y

        self.x = offset_x
        self.y = offset_y

    def set_entities(self, player, enemies, pipes):
        self.player = player
        self.enemies = enemies
        self.pipes = pipes

    def should_remove(self) -> bool:
        """
        Check if the bullet should be removed from the game.
        :return: True if the bullet should be removed, False otherwise
        """
        # remove the bullet if it flew (far) out of the game window
        # approximate range between -200 and 1230 is bouncable - roughly where the furthest pipes are
        # (right side of first pipe: -200, left side of last pipe: 1230)
        # + 60 extra for bullet's velocity and just to be safe
        if self.x > 1290 or self.x < -260 or \
           self.y < -self.h:  # the moment the bullet goes above the screen, remove it (the player can technically go
            #  up to -120, but he's guaranteed to hit a pipe there, so removing bullets early shouldn't change much
            # or self.y > self.config.window.height:  <- this should never happen as the bullet gets stopped when it hits the floor
            return True

        # remove the bullet if it hit the player or any of the enemies
        if self.hit_entity in ['player', 'enemy']:
            return True

        return False

    def handle_collision(self) -> None:
        if self.stopped:
            return

        # stop the bullet if it hits the floor
        if self.y > self.config.window.height - 163 - self.h / 2:
            self.hit_entity = 'floor'
            self.move_with_background()
            return

        # TODO maybe make the bullets bounce only once every few hits? Like 20% bounce rate?
        # bounce the bullet if it hits a pipe for the first time
        for pipe in self.pipes if not self.bounced else []:
            if not self.collide(pipe):
                continue

            if self.handle_pipe_collision(pipe):
                self.hit_entity = 'pipe'
                return

        # handle hitting enemies
        for enemy in self.enemies:
            if not self.collide(enemy):
                continue
            if enemy == self.entity and not self.bounced:  # the enemy can't hit itself unless the bullet bounces
                continue

            self.hit_entity = 'enemy'
            enemy.deal_damage(self.damage)
            return

        # handle hitting player
        if self.player and self.collide(self.player):
            self.hit_entity = 'player'
            self.player.deal_damage(self.damage)
            self.config.sounds.play(self.config.sounds.hit_bullet)
            return

    def stop(self):
        self.stopped = True
        self.velocity = pygame.Vector2(0, 0)

    def move_with_background(self):
        self.stopped = True
        self.velocity = self.VISUAL_BACKGROUND_VELOCITY

    def calculate_bullet_front_position(self) -> pygame.Vector2:
        angle_rad = math.radians(-self.angle)

        # calculate the offsets for the front point when the angle is 0
        offset_x = self.original_image_dimensions.x / 2 if not self.flipped else -self.original_image_dimensions.x / 2
        # offset_y = 0  # no vertical offset since we're starting from the center

        rotated_offset_x = offset_x * math.cos(angle_rad)  # - offset_y * math.sin(angle_rad)  # no need as offset_y = 0
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
        if (self.prev_front_pos.y < pipe.y + TOLERANCE or self.prev_front_pos.y > pipe.y + pipe.h - TOLERANCE) and \
           (self.prev_front_pos.x < pipe.x + TOLERANCE or self.prev_front_pos.x > pipe.x + pipe.w - TOLERANCE) and \
           self.is_pipe_corner_hit(pipe):
            self.bounce(True, True)
            return True

        bfp = self.calculate_bullet_front_position()

        # calculate intersection points with each side of the pipe
        if self.velocity.x == 0:
            intersection_left = intersection_right = pygame.Vector2(-1000, -1000)
        else:
            intersection_left = pygame.Vector2(pipe.x, bfp.y + self.velocity.y * ((pipe.x - bfp.x) / self.velocity.x))
            intersection_right = pygame.Vector2(pipe.x + pipe.w, bfp.y + self.velocity.y * ((pipe.x + pipe.w - bfp.x) / self.velocity.x))

        if self.velocity.y == 0:
            intersection_top = intersection_bottom = pygame.Vector2(-1000, -1000)
        else:
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

        if self.config.debug:
            self.intersections["valid"] = valid_intersections
            self.intersections["invalid"] = [i for i in [intersection_left, intersection_right, intersection_top, intersection_bottom] if i not in valid_intersections]

        closest = None
        if valid_intersections:
            closest = min(valid_intersections, key=lambda intersection: (intersection - self.prev_front_pos).length_squared())

        if closest in [intersection_left, intersection_right]:
            self.bounce(True, False)
        elif closest in [intersection_top, intersection_bottom]:
            self.bounce(False, True)

        return True

    def bounce(self, flip_x: bool, flip_y: bool) -> None:
        self.bounced = True

        if flip_x:
            self.angle = (-self.angle - 180) % 360
            # this formula basically, we just used VISUAL_BACKGROUND_VELOCITY.x instead of camera and entity velocity,
            # because: VISUAL_BACKGROUND_VELOCITY.x = -REAL_CAMERA_VELOCITY.x = -REAL_ENTITY_VELOCITY.x = -7.5
            #   VISUAL_BULLET_VELOCITY.x = -(RAW_BULLET_VELOCITY.x + REAL_ENTITY_VELOCITY.x + REAL_CAMERA_VELOCITY.x)
            self.velocity.x = -self.velocity.x + self.VISUAL_BACKGROUND_VELOCITY.x * 2  # once to cancel the background velocity, once to move against it
            self.velocity.x *= 0.9  # apply restitution factor to reduce speed after bouncing
        if flip_y:
            # self.angle = -math.degrees(math.atan2(self.velocity.y, self.velocity.x))
            self.angle = -self.angle
            self.velocity.y = -self.velocity.y
            self.velocity.y *= 0.9  # apply restitution factor to reduce speed after bouncing

        self.update_image(pygame.transform.rotate(self.original_image, self.angle))

    def is_pipe_corner_hit(self, pipe, tolerance=3.0) -> bool:
        # figure out which corner of the pipe was possibly hit
        pipe_corner: pygame.Vector2 = pygame.Vector2(pipe.x, pipe.y + pipe.h)

        # bottom left corner
        if self.prev_front_pos.y > pipe.y + pipe.h - tolerance and self.prev_front_pos.x < pipe.x + tolerance:
            pipe_corner = pygame.Vector2(pipe.x, pipe.y + pipe.h)
        # top left corner
        elif self.prev_front_pos.y < pipe.y + tolerance and self.prev_front_pos.x < pipe.x + tolerance:
            pipe_corner = pygame.Vector2(pipe.x, pipe.y)
        # bottom right corner
        elif self.prev_front_pos.y > pipe.y + pipe.h - tolerance and self.prev_front_pos.x > pipe.x + pipe.w - tolerance:
            pipe_corner = pygame.Vector2(pipe.x + pipe.w, pipe.y + pipe.h)
        # top right corner
        elif self.prev_front_pos.y < pipe.y + tolerance and self.prev_front_pos.x > pipe.x + pipe.w - tolerance:
            pipe_corner = pygame.Vector2(pipe.x + pipe.w, pipe.y)

        current_front_pos = self.calculate_bullet_front_position()
        tolerance2 = self.bullet_front_length / 2 + 3  # 3 = tolerance
        return self.is_point_on_line(self.prev_front_pos, current_front_pos, pipe_corner, tolerance2)

    @staticmethod
    def is_point_on_line(p1, p2, p3, tolerance=1.0) -> bool:
        # calculate the coefficients of the line passing through point1 and point2: Ax + By + C = 0
        A = p2.y - p1.y
        B = p1.x - p2.x
        C = p1.y * (p2.x - p1.x) - p1.x * (p2.y - p1.y)

        # calculate the distance of point3 from the line using the formula for distance
        distance = abs(A * p3.x + B * p3.y + C) / ((A ** 2 + B ** 2) ** 0.5)

        return distance <= tolerance
