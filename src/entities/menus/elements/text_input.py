import pygame

from src.utils import GameConfig, Fonts, get_font, flappy_text, apply_outline_and_shadow
from src.entities.entity import Entity


# TODO: scroll text if it's too long and add "..." at the start/end


class TextInput(Entity):
    def __init__(self, config: GameConfig, x=0, y=0, width=200, height=50, label="", font_size=42,
                 background_color_focused=(255, 255, 255), background_color_unfocused=(235, 235, 235), text_color=(0, 0, 0),
                 outline_width=4, initial_text="", max_length: int = 30,
                 on_text_change: callable = None
                 ):
        super().__init__(config=config, x=x, y=y, w=width, h=height)

        self.label = label
        self.font = get_font(Fonts.FONT_FLAPPY, font_size)
        self.label_font = get_font(Fonts.FONT_FLAPPY, 32)
        self.font_size = font_size
        self.text = initial_text
        self.background_color_focused = background_color_focused
        self.background_color_unfocused = background_color_unfocused
        self.text_color = text_color
        self.outline_width = outline_width
        self.max_length = max_length
        self.on_text_change = on_text_change
        self.focused = False
        self.cursor_visible = False
        self.last_blink_time = pygame.time.get_ticks()

    def tick(self):
        if self.focused:
            current_time = pygame.time.get_ticks()
            if current_time - self.last_blink_time > 400:
                self.cursor_visible = not self.cursor_visible
                self.last_blink_time = current_time
        super().tick()

    def draw(self):
        OUTLINE_WIDTH = 3

        # Draw the background
        bg_surface = pygame.Surface((self.w, self.h), pygame.SRCALPHA)
        bg_surface.fill(self.background_color_focused if self.focused else self.background_color_unfocused)
        self.config.screen.blit(apply_outline_and_shadow(bg_surface, outline_width=OUTLINE_WIDTH, shadow_distance=(3, 3)), (self.x, self.y))

        # Draw the text
        input_surface = self.font.render(self.text, True, self.text_color)
        text_rect = input_surface.get_rect(midleft=(self.x + 10, self.y + self.h // 2 + OUTLINE_WIDTH))
        self.config.screen.blit(input_surface, text_rect)

        # Draw blinking cursor if focused
        if self.focused and self.cursor_visible:
            cursor_x = text_rect.right
            cursor_y = text_rect.bottom - 10
            cursor_width = int(self.font_size * 0.5)
            pygame.draw.line(self.config.screen, self.text_color, (cursor_x, cursor_y), (cursor_x + cursor_width, cursor_y), int(self.font_size * 0.2) or 1)

        # Draw the label
        text_surface = flappy_text(text=self.label, font=self.label_font, text_color=(255, 255, 255),
                                   outline_color=(0, 0, 0), outline_width=3, shadow_distance=(3, 3))
        text_rect = text_surface.get_rect(topleft=(self.x, self.y - 47))
        self.config.screen.blit(text_surface, text_rect)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            self.set_focused(self.rect.collidepoint(event.pos))
        elif event.type == pygame.KEYDOWN and self.focused:
            if event.key in [pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_TAB, pygame.K_ESCAPE]:
                self.set_focused(False)
            elif event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
            else:
                self.text += event.unicode
                self.text = self.text[:self.max_length]
        if self.on_text_change:
            self.on_text_change(self.text)

    def set_focused(self, focused: bool):
        self.focused = focused
        if focused:
            pygame.key.set_repeat(400, 50)
            self.last_blink_time = pygame.time.get_ticks()
            self.cursor_visible = True
        else:
            pygame.key.set_repeat(0, 0)
