from src.utils import GameConfig
from .menu import Menu
from .menu_manager import MenuManager
from .settings_menu import SettingsMenu
from .elements import Button


# TODO: add main label to the menu - as an element
#  maybe underlined text or something like that, or just text and a line under it separating it from other elements

class MainMenu(Menu):
    def __init__(self, config: GameConfig, menu_manager: MenuManager):
        super().__init__(config, menu_manager)
        self.init_elements()

    def init_elements(self):
        button = Button(config=self.config, label="Play")
        button2 = Button(config=self.config, label="Leaderboard")
        button3 = Button(config=self.config, label="Settings", on_click=self.show_settings)
        self.add_element(button, 0, 100)
        self.add_element(button2, 0, 250)
        self.add_element(button3, 0, 400)

    def show_settings(self):
        settings_menu = SettingsMenu(self.config, self.menu_manager)
        self.menu_manager.push_menu(settings_menu)
