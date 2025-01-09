import pygame

from src.utils import GameConfig
from src.entities.entity import Entity
from .button import Button


class Tabs(Entity):
    def __init__(self, config: GameConfig, menu, tabs: dict[str, list[dict]], x=0, y=0, width=476, height=60):
        super().__init__(config=config, x=x, y=y, w=width, h=height)
        self.tabs = tabs
        self.menu = menu
        self.current_tab = list(tabs.keys())[-1]
        self.tab_buttons = {}
        self.init_tabs()
        self.switch_tab(list(tabs.keys())[0])

    def init_tabs(self):
        total_width = self.w
        total_height = self.h

        tab_width = total_width // len(self.tabs)
        tab_start_x = -total_width // 2  # center the tabs horizontally

        for i, tab_name in enumerate(self.tabs.keys()):
            x_pos = tab_start_x + (i * tab_width) + (tab_width // 2)

            button = Button(
                config=self.config,
                label=tab_name,
                on_click=lambda name=tab_name: self.switch_tab(name),
                background_color=(83, 56, 71, 255 if i == 0 else 150),
                height=total_height,
                width=tab_width,
                font_size=32,
                outline_width=3,
                shadow_distance=(3, 3)
            )

            self.menu.add_element(button, x_pos, 0)
            self.tab_buttons[tab_name] = button

    def tick(self):
        super().tick()

    def draw(self):
        super().draw()

        # Draw the bottom line
        line = pygame.Surface((self.w, 10))
        line.fill((83, 56, 71))
        self.config.screen.blit(line, (self.x, self.y + self.h - 100))  # -100 is hardcoded and not always correct

    def switch_tab(self, tab_name: str):
        if self.current_tab == tab_name:
            return

        # remove all elements from the current tab
        for element_info in self.tabs[self.current_tab]:
            element = element_info["element"]
            if element in self.menu.elements:
                self.menu.remove_element(element)

        # add all elements from the new tab
        for element_info in self.tabs[tab_name]:
            element = element_info["element"]
            x = element_info["x"]
            y = element_info["y"] + 45  # move elements down to make space for the tabs
            align = element_info["align"]
            self.menu.add_element(element, x, y, align)

        self.tab_buttons[tab_name].change_background_color((83, 56, 71, 255))
        self.tab_buttons[self.current_tab].change_background_color((83, 56, 71, 150))

        self.current_tab = tab_name
