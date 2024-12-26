import numpy as np

import pygame

from .vector import Vector2
from .constants import *


class Pellet:
    def __init__(self, row, column):
        self.name = PELLET
        self.position = Vector2(column*TILEWIDTH, row*TILEHEIGHT)
        self.color = WHITE
        self.radius = int(2 * TILEWIDTH / 16)
        self.collide_radius = 2 * TILEWIDTH / 16
        self.points = 10
        self.visible = True
        
    def render(self, screen):
        if self.visible:
            adjust = Vector2(TILEWIDTH, TILEHEIGHT) / 2
            p = self.position + adjust
            pygame.draw.circle(screen, self.color, p.as_int(), self.radius)


class PowerPellet(Pellet):
    def __init__(self, row, column):
        super().__init__(row, column)
        self.name = POWERPELLET
        self.radius = int(8 * TILEWIDTH / 16)
        self.points = 50
        self.flashTime = 0.2
        self.timer = 0
        
    def update(self, dt):
        self.timer += dt
        if self.timer >= self.flashTime:
            self.visible = not self.visible
            self.timer = 0


class PelletGroup:
    def __init__(self, pellet_file):
        self.pellet_list = []
        self.power_pellets = []
        self.create_pellet_list(pellet_file)
        self.num_eaten = 0

    def update(self, dt):
        for power_pellet in self.power_pellets:
            power_pellet.update(dt)
                
    def create_pellet_list(self, pellet_file):
        data = self.read_pelletfile(pellet_file)
        for row in range(data.shape[0]):
            for col in range(data.shape[1]):
                if data[row][col] in ['.', '+']:
                    self.pellet_list.append(Pellet(row, col))
                elif data[row][col] in ['P', 'p']:
                    pp = PowerPellet(row, col)
                    self.pellet_list.append(pp)
                    self.power_pellets.append(pp)

    @staticmethod
    def read_pelletfile(text_file):
        return np.loadtxt(f"assets/levels/{text_file}", dtype='<U1')

    def is_empty(self):
        return len(self.pellet_list) == 0

    def render(self, screen):
        for pellet in self.pellet_list:
            pellet.render(screen)
