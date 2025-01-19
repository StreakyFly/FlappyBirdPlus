import pygame

from src.utils import GameConfig, Fonts, get_font
from src.entities.entity import Entity


class Leaderboard(Entity):
    def __init__(self, config: GameConfig, x=0, y=0, width=300, height=300, data: list[dict] = None, column_info: dict = None):
        super().__init__(config=config, x=x, y=y, w=width, h=height)
        column_info = column_info or {}
        data = data or []
        self.data = data
        self.column_info = column_info

        self.font = get_font(Fonts.FONT_FLAPPY, 24)
        self.header_height = 38
        self.row_height = 30
        self.column_widths = self.compute_column_widths()

        # Colors
        self.text_color = (255, 255, 255)
        self.bg_color = (64, 43, 54)
        self.row_color = (83, 56, 71)
        self.highlight_color = (110, 72, 93)

        # Scrolling
        self.dragging = False
        self.drag_start_y = None
        self.curr_drag_y = None
        self.prev_drag_y = None
        self.scroll_offset = 0
        self.smooth_scroll_offset = 0
        self.initial_scroll_offset = None
        self.max_scroll_offset = max(0, ((len(self.data) - (self.h - self.header_height) // self.row_height) * self.row_height))
        self.scroll_velocity = 0  # current scrolling speed
        self.min_scroll_velocity = 1  # minimum velocity to stop scrolling
        self.friction = 0.95  # friction to reduce velocity each frame

        # Leaderboard surface
        self.surface = pygame.Surface((width, height))

    def tick(self):
        self.update_smooth_scroll()
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
        """ Handles scrolling and click&drag events for the leaderboard. """
        if event.type == pygame.MOUSEBUTTONDOWN:
            self.reset_smooth_scroll()
            if event.button == 4:  # scroll up
                self.scroll_offset = max(self.scroll_offset - self.row_height, 0)
            elif event.button == 5:  # scroll down
                self.scroll_offset = min(self.scroll_offset + self.row_height, self.max_scroll_offset)
            elif event.button == 1 and self.rect.collidepoint(event.pos):  # left mouse button clicked on the leaderboard
                self.dragging = True
                self.scroll_velocity = 0  # reset velocity when drag starts
                self.drag_start_y = event.pos[1]  # initial y-coordinate of the drag
                self.initial_scroll_offset = self.scroll_offset  # current scroll offset
                pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_HAND)

        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1 and self.dragging:  # left mouse button released
                self.dragging = False
                pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)
                if self.prev_drag_y is not None:  # calculate velocity based on last drag movement
                    self.scroll_velocity = -(event.pos[1] - self.prev_drag_y) * 3

        elif event.type == pygame.MOUSEMOTION:
            if self.dragging:
                delta_y = event.pos[1] - self.drag_start_y
                self.scroll_offset = self.initial_scroll_offset - ((delta_y // self.row_height) * self.row_height)
                self.scroll_offset = pygame.math.clamp(self.scroll_offset, 0, self.max_scroll_offset)
                self.smooth_scroll_offset = self.scroll_offset
                self.prev_drag_y = self.curr_drag_y
                self.curr_drag_y = event.pos[1]

    def update_smooth_scroll(self):
        """ Handles smooth scrolling logic after the user releases the drag. """
        if not self.dragging and abs(self.scroll_velocity) > self.min_scroll_velocity:
            self.smooth_scroll_offset += self.scroll_velocity
            self.scroll_offset = round(self.smooth_scroll_offset / self.row_height) * self.row_height  # snap to the nearest row
            self.scroll_offset = pygame.math.clamp(self.scroll_offset, 0, self.max_scroll_offset)
            self.scroll_velocity *= self.friction  # apply friction to reduce velocity

            if abs(self.scroll_velocity) < self.min_scroll_velocity:
                self.reset_smooth_scroll()

    def reset_smooth_scroll(self):
        """ Resets the smooth scrolling state. """
        self.scroll_velocity = 0

    def set_data(self, data, column_info=None):
        """ Updates the leaderboard data and column info. """
        self.data = data
        if column_info is not None:
            self.column_info = column_info
            self.column_widths = self.compute_column_widths()
        # Update the maximum scroll offset based on the new data
        self.max_scroll_offset = max(0, ((len(self.data) - (self.h - self.header_height) // self.row_height) * self.row_height))

    def compute_column_widths(self):
        """ Computes the width of each column based on the column weights. """
        total_weight = sum(info["weight"] for info in self.column_info.values())
        return {
            column: self.w * (info["weight"] / total_weight)
            for column, info in self.column_info.items()
        }
