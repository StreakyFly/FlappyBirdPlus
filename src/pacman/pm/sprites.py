import numpy as np

import pygame

from .constants import *
from src.utils import load_image, animation_spritesheet_to_frames, Animation

BASETILEWIDTH = 16
BASETILEHEIGHT = 16
DEATH = 5


class Spritesheet:
    def __init__(self):
        self.sheet = pygame.image.load("assets/images/pacman/spritesheet.png").convert_alpha()
        width = int(self.sheet.get_width() / BASETILEWIDTH * TILEWIDTH)
        height = int(self.sheet.get_height() / BASETILEHEIGHT * TILEHEIGHT)
        self.sheet = pygame.transform.scale(self.sheet, (width, height))
        
    def get_image(self, x, y, width, height):
        x *= TILEWIDTH
        y *= TILEHEIGHT
        self.sheet.set_clip(pygame.Rect(x, y, width, height))
        return self.sheet.subsurface(self.sheet.get_clip())


class PacmanSprites(Spritesheet):
    def __init__(self, entity):
        super().__init__()
        self.entity = entity
        self.animations = {}
        self.stop_images = {}
        self.load_animations()
        self.stop_image: pygame.Surface = self.stop_images[LEFT]
        self.entity.image = self.get_start_image()

    def load_animations(self):
        player_sheet = animation_spritesheet_to_frames(load_image("pacman/player", True), 4)
        left = [pygame.transform.flip(frame, True, False) for frame in player_sheet]
        right = player_sheet
        up = [pygame.transform.rotate(frame, 90) for frame in player_sheet]
        down = [pygame.transform.rotate(frame, -90) for frame in player_sheet]
        self.stop_images = {LEFT: left[0], RIGHT: right[0], UP: up[0], DOWN: down[0]}
        self.animations[LEFT] = Animation(left[1:], frame_duration=5)  # had speed 20 (1/20)
        self.animations[RIGHT] = Animation(right[1:], frame_duration=5)  # had speed 20 (1/20)
        self.animations[UP] = Animation(up[1:], frame_duration=5)  # had speed 20 (1/20)
        self.animations[DOWN] = Animation(down[1:], frame_duration=5)  # had speed 20 (1/20)
        self.animations[DEATH] = Animation(left[1:], frame_duration=5, loop=False)  # TODO: death animation, had speed 6 (1/6)

    def update(self):
        if self.entity.alive:
            if self.entity.direction == LEFT:
                self.entity.image = self.animations[LEFT].update()
                self.stop_image = self.stop_images[LEFT]
            elif self.entity.direction == RIGHT:
                self.entity.image = self.animations[RIGHT].update()
                self.stop_image = self.stop_images[RIGHT]
            elif self.entity.direction == DOWN:
                self.entity.image = self.animations[DOWN].update()
                self.stop_image = self.stop_images[DOWN]
            elif self.entity.direction == UP:
                self.entity.image = self.animations[UP].update()
                self.stop_image = self.stop_images[UP]
            elif self.entity.direction == STOP:
                self.entity.image = self.stop_image
        else:
            self.entity.image = self.animations[DEATH].update()

    def reset(self):
        for key in list(self.animations.keys()):
            self.animations[key].reset()

    def get_start_image(self):
        return self.stop_image


class GhostSprites(Spritesheet):
    def __init__(self, entity):
        super().__init__()
        self.x = {BLINKY:0, PINKY:2, INKY:4, CLYDE:6}
        self.entity = entity
        self.entity.image = self.get_start_image()

    def update(self):
        x = self.x[self.entity.name]
        if self.entity.mode.current in [SCATTER, CHASE]:
            if self.entity.direction == LEFT:
                self.entity.image = self.get_image(x, 8)
            elif self.entity.direction == RIGHT:
                self.entity.image = self.get_image(x, 10)
            elif self.entity.direction == DOWN:
                self.entity.image = self.get_image(x, 6)
            elif self.entity.direction == UP:
                self.entity.image = self.get_image(x, 4)
        elif self.entity.mode.current == FREIGHT:
            self.entity.image = self.get_image(10, 4)
        elif self.entity.mode.current == SPAWN:
            if self.entity.direction == LEFT:
                self.entity.image = self.get_image(8, 8)
            elif self.entity.direction == RIGHT:
                self.entity.image = self.get_image(8, 10)
            elif self.entity.direction == DOWN:
                self.entity.image = self.get_image(8, 6)
            elif self.entity.direction == UP:
                self.entity.image = self.get_image(8, 4)
               
    def get_start_image(self):
        return self.get_image(self.x[self.entity.name], 4)

    def get_image(self, x, y):
        return Spritesheet.get_image(self, x, y, 2 * TILEWIDTH, 2 * TILEHEIGHT)


class FruitSprites(Spritesheet):
    def __init__(self, entity, level):
        super().__init__()
        self.entity = entity
        self.fruits = {0:(16,8), 1:(18,8), 2:(20,8), 3:(16,10), 4:(18,10), 5:(20,10)}
        self.entity.image = self.get_start_image(level % len(self.fruits))

    def get_start_image(self, key):
        return self.get_image(*self.fruits[key])

    def get_image(self, x, y):
        return Spritesheet.get_image(self, x, y, 2 * TILEWIDTH, 2 * TILEHEIGHT)


class LifeSprites(Spritesheet):
    def __init__(self, numlives):
        super().__init__()
        self.reset_lives(numlives)

    def remove_image(self):
        if len(self.images) > 0:
            self.images.pop(0)

    def reset_lives(self, numlives):
        self.images = []
        for i in range(numlives):
            self.images.append(self.get_image(0, 0))

    def get_image(self, x, y):
        return Spritesheet.get_image(self, x, y, 2 * TILEWIDTH, 2 * TILEHEIGHT)


class MazeSprites(Spritesheet):
    def __init__(self, maze_file, rot_file):
        super().__init__()
        self.data = self.read_maze_file(maze_file)
        self.rot_data = self.read_maze_file(rot_file)

    def get_image(self, x, y):
        return Spritesheet.get_image(self, x, y, TILEWIDTH, TILEHEIGHT)

    @staticmethod
    def read_maze_file(maze_file):
        return np.loadtxt(f"assets/levels/{maze_file}", dtype='<U1')

    def construct_background(self, background, y):
        for row in list(range(self.data.shape[0])):
            for col in list(range(self.data.shape[1])):
                if self.data[row][col].isdigit():
                    x = int(self.data[row][col]) + 12
                    sprite = self.get_image(x, y)
                    rotval = int(self.rot_data[row][col])
                    sprite = self.rotate(sprite, rotval)
                    background.blit(sprite, (col*TILEWIDTH, row*TILEHEIGHT))
                elif self.data[row][col] == '=':
                    sprite = self.get_image(10, 8)
                    background.blit(sprite, (col*TILEWIDTH, row*TILEHEIGHT))
        return background

    @staticmethod
    def rotate(sprite, value):
        return pygame.transform.rotate(sprite, value*90)
