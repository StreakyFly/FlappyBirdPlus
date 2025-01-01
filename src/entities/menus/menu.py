import pygame

from src.utils import GameConfig, Fonts, get_font, flappy_text, apply_outline_and_shadow
from src.entities.entity import Entity
from .menu_manager import MenuManager
from .elements import Button


# TODO: create a proper design for the menu


class Menu(Entity):
    SIDE_PADDING = 40
    TITLEBAR_HEIGHT = 100

    def __init__(self, config: GameConfig, menu_manager: MenuManager, name: str = ""):
        image = config.images.user_interface['menu']
        super().__init__(
            config=config,
            image=image,
            x=(config.window.width - image.get_width()) // 2,
            y=(config.window.height - image.get_height()) // 2,
        )
        self.menu_manager = menu_manager
        self.name = name

        self.elements: list = []

        # Titlebar
        self.font = None
        self.back_button = None
        self.init_titlebar()

    def init_titlebar(self):
        if self.name:
            self.font = get_font(Fonts.FONT_FLAPPY, 48)
            self.back_button = Button(config=self.config, x=self.x, y=self.y, width=100, height=100, background_color=(0, 0, 0, 0),
                                      label="<", on_click=self.menu_manager.pop_menu, outline_width=3)
            self.elements.append(self.back_button)

    def tick(self):
        super().tick()
        for element in self.elements:
            element.tick()

    def draw(self):
        super().draw()

        # Draw the titlebar, if name is set
        if self.name:
            text_surface = flappy_text(text=self.name, font=self.font, text_color=(255, 255, 255),
                                       outline_color=(0, 0, 0), outline_width=4, shadow_distance=(4, 4))
            text_rect = text_surface.get_rect(center=(self.x + self.w // 2, self.y + text_surface.get_height() // 2 + 20))
            self.config.screen.blit(text_surface, text_rect)
            # TODO: draw bottom line of the titlebar for separation
            line = pygame.Surface((self.w, 10))
            line.fill((83, 56, 71))
            self.config.screen.blit(line, (self.x, self.y + self.TITLEBAR_HEIGHT - 10))

    def add_element(self, element, x, y, align="center"):
        match align:
            case "center":
                element.x = x + self.x + (self.w // 2 - element.w // 2)
            case "left":
                element.x = x + self.x + self.SIDE_PADDING
            case "right":
                element.x = x + self.x + self.w - element.w - self.SIDE_PADDING
            case _:
                raise ValueError(f"Invalid alignment: {align}")

        element.y = y + self.y
        if self.name:
            element.y += self.TITLEBAR_HEIGHT

        # If the element has an init method, call it, as it may need to set up some things based on its new position
        if hasattr(element, "init"):
            element.init()
        self.elements.append(element)

    def handle_event(self, event):
        if self.name:
            # Go back to the previous menu when ESC is pressed
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self.menu_manager.pop_menu()
                return

        for element in self.elements:
            if hasattr(element, "handle_event"):
                element.handle_event(event)
