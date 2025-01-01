import pygame

from src.utils import GameConfig, Fonts, load_font, flappy_text, apply_outline_and_shadow
from src.entities.entity import Entity


class Toggle(Entity):
    def __init__(self, config: GameConfig, x=0, y=0, width=80, height=40, label: str = "",
                 on_toggle: callable = None, initial_state=False
                 ):
        image = pygame.Surface((width, height), pygame.SRCALPHA)
        super().__init__(config=config, image=image, x=x, y=y)
        self.label = label
        self.on_toggle_callback = on_toggle
        self.state = initial_state
        self.font = load_font(Fonts.FONT_FLAPPY, 32)
        self.hovered = False

        # Animation stuff
        self.animating = False
        self.animation_progress = 0
        self.animation_duration = 6
        self.start_x, self.end_x = None, None
        self.init()

    def init(self):
        self.start_x = self.x
        self.end_x = self.x + (self.w - self.h) if self.state else self.x

    def tick(self):
        self.check_hover()
        self.update_animation()
        super().tick()

    def draw(self):
        super().draw()

        # Draw the toggle background
        bg_color = (190, 220, 190) if self.state else (220, 190, 190)
        self.image.fill(bg_color)
        combined_surface = apply_outline_and_shadow(self.image, outline_width=3, shadow_distance=(3, 3))
        self.config.screen.blit(combined_surface, (self.x, self.y))

        # Draw the toggle switch
        switch_color = (0, 255, 0) if self.state else (255, 0, 0)
        switch_x = self.get_current_switch_x()
        switch_width = self.h * 0.68
        switch_height = switch_width
        switch_surface = pygame.Surface((switch_width, switch_height), pygame.SRCALPHA)
        switch_surface.fill(switch_color)
        combined_switch_surface = apply_outline_and_shadow(switch_surface, outline_width=3, shadow_distance=(1, 1))
        self.config.screen.blit(combined_switch_surface, (switch_x + (self.h - switch_width) // 2, self.y + (self.h - switch_height) // 2))

        # Draw the label
        text_surface = flappy_text(text=self.label, font=self.font, text_color=(255, 255, 255),
                                   outline_color=(0, 0, 0), outline_width=3, shadow_distance=(3, 3))
        text_rect = text_surface.get_rect(topleft=(self.x, self.y - 47))
        self.config.screen.blit(text_surface, text_rect)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and self.hovered:
            self.toggle()

    def check_hover(self):
        mouse_pos = pygame.mouse.get_pos()
        self.hovered = self.rect.collidepoint(mouse_pos)

    def toggle(self):
        self.state = not self.state
        self.start_x = self.get_current_switch_x()
        self.end_x = self.x + (self.w - self.h) if self.state else self.x
        self.animating = True
        self.animation_progress = 0
        if self.on_toggle_callback:
            self.on_toggle_callback(self.state)

    def update_animation(self):
        if self.animating:
            self.animation_progress += 1
            if self.animation_progress >= self.animation_duration:
                self.animating = False

    def get_current_switch_x(self):
        if not self.animating:
            return self.end_x
        progress_ratio = self.animation_progress / self.animation_duration
        return self.start_x + (self.end_x - self.start_x) * progress_ratio
