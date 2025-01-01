import pygame

from src.utils import GameConfig, Fonts, get_font
from src.entities.entity import Entity


class Leaderboard(Entity):
    def __init__(self, config: GameConfig, x=0, y=0, width=300, height=300, data=None):
        super().__init__(config=config, x=x, y=y, w=width, h=height)
        if data is None:
            data = []
        self.data = data

        self.scroll_offset = 0
        self.scroll_speed = 20
        self.row_height = 30
        self.font = get_font(Fonts.FONT_FLAPPY, 24)

        self.bg_color = (30, 30, 30)
        self.text_color = (255, 255, 255)
        self.header_color = (50, 50, 50)
        self.row_color = (40, 40, 40)
        self.highlight_color = (60, 60, 60)

        self.surface = pygame.Surface((width, height))

    def tick(self):
        super().tick()

    def draw(self):
        super().draw()

        self.surface.fill(self.bg_color)

        # Draw the header
        pygame.draw.rect(self.surface, self.header_color, (0, 40, self.w, self.row_height))
        score_header = self.font.render("Score", True, self.text_color)
        date_header = self.font.render("Date", True, self.text_color)
        self.surface.blit(score_header, (10, 45))
        self.surface.blit(date_header, (self.w // 2, 45))

        # Draw the rows
        start_y = 70 - self.scroll_offset
        for index, entry in enumerate(self.data):
            row_y = start_y + index * self.row_height
            if 70 <= row_y < self.h:
                row_color = self.highlight_color if index % 2 == 0 else self.row_color
                pygame.draw.rect(self.surface, row_color, (0, row_y, self.w, self.row_height))

                # Render score and date
                score_text = self.font.render(str(entry["score"]), True, self.text_color)
                date_text = self.font.render(entry["timestamp"], True, self.text_color)
                self.surface.blit(score_text, (10, row_y + 5))
                self.surface.blit(date_text, (self.w // 2, row_y + 5))

        self.config.screen.blit(self.surface, (self.x, self.y))

    def handle_event(self, event):
        """ Handles scrolling events for the leaderboard. """
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 4:  # Scroll up
                self.scroll_offset = max(self.scroll_offset - self.scroll_speed, 0)
            elif event.button == 5:  # Scroll down
                max_scroll = max(0, len(self.data) * self.row_height - (self.h - 70))
                self.scroll_offset = min(self.scroll_offset + self.scroll_speed, max_scroll)

    def set_data(self, data):
        """ Updates the leaderboard data. """
        self.data = data
