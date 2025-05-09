import pygame

from .images import Images
from .sounds import Sounds
from .window import Window
from .persistance import SettingsManager


class GameConfig:
    def __init__(
        self,
        screen: pygame.Surface,
        clock: pygame.time.Clock,
        fps: int,
        window: Window,
        images: Images,
        sounds: Sounds,
        settings_manager: SettingsManager,
        debug: bool = False,
        save_results: bool = True,
    ) -> None:
        self.screen = screen
        self.clock = clock
        self.fps = fps
        self.window = window
        self.images = images
        self.sounds = sounds
        self.settings_manager = settings_manager
        self.debug = debug
        self.save_results = save_results

    def tick(self) -> None:
        self.clock.tick(self.fps)
