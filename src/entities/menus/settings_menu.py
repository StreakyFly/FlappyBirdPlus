from src.utils import GameConfig
from .menu import Menu
from .menu_manager import MenuManager
from .elements import Button


class SettingsMenu(Menu):
    def __init__(self, config: GameConfig, menu_manager: MenuManager):
        super().__init__(config, menu_manager)
        self.init_elements()

    def init_elements(self):
        button = Button(config=self.config, label="Back", on_click=self.menu_manager.pop_menu)
        self.add_element(button, 0, 50)
