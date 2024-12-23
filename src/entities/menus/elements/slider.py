import pygame

from src.utils import GameConfig, Fonts, load_font, flappy_text, apply_outline_and_shadow
from src.entities.entity import Entity


class Slider(Entity):
    def __init__(self, config: GameConfig, x=0, y=0, width=300, min_value=0, max_value=100, initial_value=50, label: str = ""):
        super().__init__(config=config, x=x, y=y)
        self.w = width
        self.min_value = min_value
        self.max_value = max_value
        self.value = initial_value
        self.label = label
        self.font = load_font(Fonts.FONT_FLAPPY, 32)
        self.dragging = False

        self.bar_height = 10
        self.bar_color = (210, 210, 210)
        self.handle_color = (255, 255, 255)
        self.handle_width = 15
        self.handle_height = 24

    def tick(self):
        super().tick()

    def draw(self):
        super().draw()

        # Draw the slider bar
        bar_surface = pygame.Surface((self.w, self.bar_height), pygame.SRCALPHA)
        bar_surface.fill(self.bar_color)
        combined_surface = apply_outline_and_shadow(bar_surface, outline_width=3, shadow_distance=(3, 3))
        self.config.screen.blit(combined_surface, (self.x, self.y))

        # Draw the handle
        handle_x = self.x + int((self.value - self.min_value) / (self.max_value - self.min_value) * self.w)
        handle_y = self.y + self.bar_height // 2 - self.handle_height // 2
        handle_surface = pygame.Surface((self.handle_width, self.handle_height), pygame.SRCALPHA)
        handle_surface.fill(self.handle_color)
        combined_handle_surface = apply_outline_and_shadow(handle_surface, outline_algorithm=0, outline_width=3, shadow_distance=(3, 3))
        self.config.screen.blit(combined_handle_surface, (handle_x - self.handle_width // 2, handle_y))

        # Draw the label
        text_surface = flappy_text(text=f"{self.label}: {self.value}", font=self.font, text_color=(255, 255, 255),
                                   outline_color=(0, 0, 0), outline_width=3, shadow_distance=(3, 3))
        text_rect = text_surface.get_rect(topleft=(self.x, self.y - 47))
        self.config.screen.blit(text_surface, text_rect)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.is_hovering_handle(event.pos):
                self.dragging = True
        elif event.type == pygame.MOUSEBUTTONUP:
            self.dragging = False
        elif event.type == pygame.MOUSEMOTION:
            if self.dragging:
                self.update_value(event.pos)

    def is_hovering_handle(self, mouse_pos):
        handle_x = self.x + int((self.value - self.min_value) / (self.max_value - self.min_value) * self.w)
        handle_y = self.y + self.bar_height // 2 - self.handle_height // 2
        return handle_x - self.handle_width // 2 <= mouse_pos[0] <= handle_x + self.handle_width // 2 and \
            handle_y <= mouse_pos[1] <= handle_y + self.handle_height

    def update_value(self, mouse_pos):
        relative_x = mouse_pos[0] - self.x
        self.value = self.min_value + (relative_x / self.w) * (self.max_value - self.min_value)
        self.value = int(pygame.math.clamp(self.value, self.min_value, self.max_value))
