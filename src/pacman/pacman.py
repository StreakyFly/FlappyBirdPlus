import pygame

from src.utils import GameConfig
from .images import Images
from .player import Player
from .enemy import Enemy


class Pacman:
    def __init__(self, config: GameConfig, player_id):
        self.config = config
        self.clock = pygame.time.Clock()
        self.images = Images(player_id)
        # self.sounds = None  # TODO: well... TODO?
        self.player = Player(self.config, self.images.player)
        self.enemies = [Enemy(self.config, self.images.enemy) for _ in range(4)]

    def update(self):
        # TODO
        #  update enemies
        #  update player

        self.config.screen.fill((0, 123, 0))
        pygame.draw.rect(self.config.screen, (255, 255, 0), (400, 150, 100, 100))

        self.player.tick()
        for enemy in self.enemies:
            enemy.tick()
