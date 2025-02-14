import threading
import time

import pygame
from pygame.locals import KEYDOWN, K_SPACE

from src.utils import GameConfig
from .images import Images
from .sounds import Sounds

from .pm.run import GameController


class Pacman:
    def __init__(self, config: GameConfig, player_id):
        self.config = config
        self.clock = pygame.time.Clock()
        # self.images = Images(player_id)
        volume = config.sounds.global_volume * config.sounds.sounds_volume
        self.sounds = Sounds(volume=volume)
        self.sounds.theme.play()

        threading.Thread(target=self.start_game_fr, args=(5,)).start()

        self.game = GameController(config, player_id, self.sounds)
        self.game.start_game()

    def update(self, events):
        self.game.check_events(events)
        res = self.game.update()
        if res is not None:
            return res

    def start_game_fr(self, delay):
        time.sleep(delay)
        if self.game.pause.paused:
            pygame.event.post(pygame.event.Event(KEYDOWN, key=K_SPACE))
