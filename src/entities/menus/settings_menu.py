from src.utils import GameConfig, SettingsManager
from .menu import Menu
from .menu_manager import MenuManager
from .elements import Slider, Toggle


class SettingsMenu(Menu):
    def __init__(self, config: GameConfig, menu_manager: MenuManager):
        super().__init__(config, menu_manager, name="Settings")
        self.settings_manager = SettingsManager()
        self.init_elements()

    def init_elements(self):
        volume_slider = Slider(config=self.config, label="Volume", initial_value=self.settings_manager.get_setting("volume") * 100, on_slide=self.on_volume_slide)
        vsync_toggle = Toggle(config=self.config, label="V-sync", initial_state=self.settings_manager.get_setting("vsync"), on_toggle=self.on_vsync_toggle)
        self.add_element(volume_slider, 0, 100, "left")
        self.add_element(vsync_toggle, 0, 200, "left")

    def on_volume_slide(self, value):
        self.settings_manager.update_setting("volume", value / 100)
        # TODO: set volume

    def on_vsync_toggle(self, state):
        self.settings_manager.update_setting("vsync", state)
        # TODO: set vsync
