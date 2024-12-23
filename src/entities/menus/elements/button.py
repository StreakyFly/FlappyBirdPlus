import pygame

from src.utils import GameConfig, Fonts, load_font, flappy_text
from src.entities.entity import Entity


class Button(Entity):
    def __init__(self, config: GameConfig, x=0, y=0, image=None, label: str = "", on_click: callable = None):
        image = image or config.images.user_interface['button-wide']
        super().__init__(config=config, image=image, x=x, y=y)
        self.label = label
        self.on_click_callback = on_click
        self.font = load_font(Fonts.FONT_FLAPPY, 48)
        self.hovered = False

    def tick(self):
        self.check_hover()
        super().tick()

    def draw(self):
        super().draw()

        # Change button appearance when hovered
        if self.hovered:
            # TODO: temporary hover effect, make it fancier
            text_color = (255, 255, 50)
        else:
            text_color = (255, 255, 255)

        # Draw the button label
        text_surface = flappy_text(text=self.label, font=self.font, text_color=text_color,
                                   outline_color=(0, 0, 0), outline_width=4, shadow_distance=(4, 4))
        text_rect = text_surface.get_rect(center=(self.x  + self.w // 2, self.y + self.h // 2))
        self.config.screen.blit(text_surface, text_rect)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and self.hovered:
            self.on_click()

    def check_hover(self):
        mouse_pos = pygame.mouse.get_pos()
        self.hovered = self.rect.collidepoint(mouse_pos)

    def on_click(self):
        print(f"Button '{self.label}' clicked")
        if self.on_click_callback:
            self.on_click_callback()
        else:
            print("No callback set for this button")
