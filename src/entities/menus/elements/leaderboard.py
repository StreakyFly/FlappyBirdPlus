import pygame

from src.utils import GameConfig, Fonts, get_font
from src.entities.entity import Entity


# TODO: create a proper design for the leaderboard (not black/gray and white, but more colorful)


class Leaderboard(Entity):
    def __init__(self, config: GameConfig, x=0, y=0, width=300, height=300, data: list[dict] = None, column_info: dict = None):
        super().__init__(config=config, x=x, y=y, w=width, h=height)
        if column_info is None:
            column_info = {}
        if data is None:
            data = []
        self.data = data
        self.column_info = column_info

        self.column_widths = self.compute_column_widths()

        self.scroll_offset = 0
        self.header_height = 38
        self.row_height = 30
        self.font = get_font(Fonts.FONT_FLAPPY, 24)

        self.text_color = (255, 255, 255)
        # self.bg_color = (30, 30, 30)
        # self.row_color = (40, 40, 40)
        # self.highlight_color = (60, 60, 60)
        self.bg_color = (64, 43, 54)
        self.row_color = (83, 56, 71)
        self.highlight_color = (110, 72, 93)

        self.surface = pygame.Surface((width, height))

    def tick(self):
        super().tick()

    def draw(self):
        super().draw()
        self.surface.fill(self.bg_color)

        # Draw the header
        current_x = 0
        for column, info in self.column_info.items():
            header_text = self.font.render(info['label'], True, self.text_color)
            self.surface.blit(header_text, (current_x + 10, ((self.header_height - header_text.get_height()) // 2) + 1))
            current_x += self.column_widths[column]

        # Draw the rows
        start_y = self.header_height - self.scroll_offset
        extra_entry = [{column: "\\" for column in self.column_info.keys()}] if len(self.data) == 0 else []
        for index, entry in enumerate(self.data + extra_entry):
            row_y = start_y + index * self.row_height
            if not (self.header_height <= row_y < self.h):
                continue

            row_color = self.highlight_color if index % 2 == 0 else self.row_color
            pygame.draw.rect(self.surface, row_color, (0, row_y, self.w, self.row_height))

            # Draw each column
            current_x = 0
            for column in self.column_info.keys():
                column_width = self.column_widths[column]
                text = self.font.render(str(entry[column]), True, self.text_color)
                text_x = current_x + 10
                self.surface.blit(text, (text_x, row_y + 4))
                current_x += column_width

        self.config.screen.blit(self.surface, (self.x, self.y))

    def handle_event(self, event):
        """ Handles scrolling events for the leaderboard. """
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 4:  # Scroll up
                self.scroll_offset = max(self.scroll_offset - self.row_height, 0)
            elif event.button == 5:  # Scroll down
                max_scroll = max(0, ((len(self.data) - (self.h-self.header_height) // self.row_height) * self.row_height))
                self.scroll_offset = min(self.scroll_offset + self.row_height, max_scroll)

    def set_data(self, data, column_info=None):
        """ Updates the leaderboard data and column info. """
        self.data = data
        if column_info is not None:
            self.column_info = column_info
            self.column_widths = self.compute_column_widths()

    def compute_column_widths(self):
        """ Computes the width of each column based on the column weights. """
        total_weight = sum(info["weight"] for info in self.column_info.values())
        return {
            column: self.w * (info["weight"] / total_weight)
            for column, info in self.column_info.items()
        }
