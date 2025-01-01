import pygame

from src.utils import GameConfig, Fonts, get_font, flappy_text
from src.entities.entity import Entity


class Button(Entity):
    def __init__(self, config: GameConfig, x=0, y=0, width=0, height=0, image=None, background_color=None,
                 label: str = "", on_click: callable = None, font_size: int = 48, outline_width=4, shadow_distance=(4, 4)
                 ):
        if background_color:
            image = pygame.Surface((width, height), pygame.SRCALPHA)
            image.fill(background_color)
        else:
            image = image or config.images.user_interface['button-wide']
        super().__init__(config=config, image=image, x=x, y=y, w=width, h=height)
        self.label = label
        self.on_click_callback = on_click
        self.outline_width = outline_width
        self.shadow_distance = shadow_distance
        self.font = get_font(Fonts.FONT_FLAPPY, font_size)
        self.hovered = False

    def tick(self):
        self.check_hover()
        super().tick()

    def draw(self):
        super().draw()

        # Change button appearance when hovered
        if self.hovered:
            # TODO: temporary hover effect, make it fancier
            text_color = (247, 182, 55)
        else:
            text_color = (255, 255, 255)

        # Draw the button label
        text_surface = flappy_text(text=self.label, font=self.font, text_color=text_color,
                                   outline_color=(0, 0, 0), outline_width=self.outline_width, shadow_distance=self.shadow_distance)
        text_rect = text_surface.get_rect(center=(self.x  + self.w // 2, self.y + self.h // 2))
        self.config.screen.blit(text_surface, text_rect)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and self.hovered:
            self.on_click()

    def check_hover(self):
        mouse_pos = pygame.mouse.get_pos()
        self.hovered = self.rect.collidepoint(mouse_pos)

    def on_click(self):
        if self.on_click_callback:
            self.on_click_callback()
        else:
            print(f"No on_click callback set for button '{self.label}'")
