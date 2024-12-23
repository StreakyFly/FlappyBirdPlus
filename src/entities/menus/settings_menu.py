from src.utils import GameConfig
from .menu import Menu
from .menu_manager import MenuManager
from .elements import Button, Slider, Toggle


class SettingsMenu(Menu):
    def __init__(self, config: GameConfig, menu_manager: MenuManager):
        super().__init__(config, menu_manager)
        self.init_elements()

    def init_elements(self):
        back_button = Button(config=self.config, label="Back", on_click=self.menu_manager.pop_menu)
        volume_slider = Slider(config=self.config, label="Volume")
        vsync_toggle = Toggle(config=self.config, label="V-sync")
        self.add_element(back_button, 0, 450)
        self.add_element(volume_slider, 0, 100, "left")
        self.add_element(vsync_toggle, 0, 200, "left")
