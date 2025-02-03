import threading
import time

import pygame
from pygame.locals import KEYDOWN, K_SPACE

from src.utils import GameConfig
from .images import Images
from .player import Player

from .pm.run import GameController


class Pacman:
    def __init__(self, config: GameConfig, player_id):
        self.config = config
        self.clock = pygame.time.Clock()
        # self.images = Images(player_id)
        # self.sounds = None  # TODO: well... TODO?
        # self.player = Player(self.config, self.images.player)

        theme = pygame.mixer.Sound('assets/audio/pacman/theme.mp3')
        theme.play()

        threading.Thread(target=self.start_game_fr, args=(5,)).start()

        self.game = GameController(config, player_id)
        self.game.start_game()

    def update(self, events):
        self.game.check_events(events)
        self.game.update()

        # self.config.screen.fill((0, 123, 0))
        # pygame.draw.rect(self.config.screen, (255, 255, 0), (400, 150, 100, 100))
        #
        # self.player.tick()

    def start_game_fr(self, delay):
        time.sleep(delay)
        pygame.event.post(pygame.event.Event(KEYDOWN, key=K_SPACE))
