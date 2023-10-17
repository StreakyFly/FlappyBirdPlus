import pygame

from ..utils import GameConfig, Fonts, flappy_text, load_font
from .entity import Entity


class Score(Entity):
    text_cache = {}
    max_cache_size = 100

    def __init__(self, config: GameConfig) -> None:
        super().__init__(config)
        self.y = self.config.window.height * 0.04
        self.score = 0

        self.font = load_font(Fonts.FONT_FLAPPY, 76)

    def reset(self) -> None:
        self.score = 0

    def add(self) -> None:
        self.score += 1
        self.config.sounds.point.play()

    @property
    def rect(self) -> pygame.Rect:
        text_surface = flappy_text(text=str(self.score), font=self.font, text_color=(255, 255, 255),
                                   outline_color=(0, 0, 0), outline_width=5, shadow_distance=(5, 5))
        text_rect = text_surface.get_rect()
        text_rect.centerx = self.config.window.width // 2
        text_rect.y = self.y
        return text_rect

    def draw(self) -> None:
        if self.score not in Score.text_cache:
            text_surface = flappy_text(text=str(self.score), font=self.font, text_color=(255, 255, 255),
                                       outline_color=(0, 0, 0), outline_width=5, shadow_distance=(5, 5))

            # Store the rendered text in the cache
            Score.text_cache[self.score] = text_surface

            # Check the cache size and remove the second-newest entry if necessary
            if len(Score.text_cache) > Score.max_cache_size:
                scores = list(Score.text_cache.keys())
                second_newest_score = scores[-2]
                del Score.text_cache[second_newest_score]

        # Use the pre-rendered text from the cache
        combined_surface = Score.text_cache[self.score]

        text_rect = combined_surface.get_rect()
        text_rect.centerx = self.config.window.width // 2
        text_rect.y = self.y

        self.config.screen.blit(combined_surface, text_rect)
