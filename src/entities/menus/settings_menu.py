from src.utils import GameConfig, SettingsManager
from .menu import Menu
from .menu_manager import MenuManager
from .elements import Slider, Toggle, Tabs


class SettingsMenu(Menu):
    def __init__(self, config: GameConfig, menu_manager: MenuManager):
        super().__init__(config, menu_manager, name="Settings")
        self.settings_manager = SettingsManager()
        self.init_elements()

    def init_elements(self):
        volume_slider = Slider(config=self.config, label="Volume", initial_value=self.settings_manager.get_setting("volume") * 100, on_slide=self.on_volume_slide)
        vsync_toggle = Toggle(config=self.config, label="V-sync", initial_state=self.settings_manager.get_setting("vsync"), on_toggle=self.on_vsync_toggle)
        ai_player_toggle = Toggle(config=self.config, label="AI Player", initial_state=self.settings_manager.get_setting("ai_player"), on_toggle=self.on_ai_player_toggle)
        pacman_toggle = Toggle(config=self.config, label="Pacman on death", initial_state=self.settings_manager.get_setting("pacman"), on_toggle=self.on_pacman_toggle)
        debug_toggle = Toggle(config=self.config, label="Debug mode", initial_state=self.settings_manager.get_setting("debug"), on_toggle=self.on_debug_toggle)
        tabs = Tabs(config=self.config, menu=self, tabs={
                        "General": [
                            {"element": volume_slider, "x": 0, "y": 100, "align": "left"},
                            {"element": vsync_toggle, "x": 0, "y": 220, "align": "left"},
                        ],
                        "Gameplay": [
                            {"element": ai_player_toggle, "x": 0, "y": 100, "align": "left"},
                            {"element": pacman_toggle, "x": 0, "y": 220, "align": "left"},
                            {"element": debug_toggle, "x": 0, "y": 340, "align": "left"},
                        ],
                    })
        self.add_element(tabs, 0, 100, "center")

    def on_volume_slide(self, value):
        self.settings_manager.update_setting("volume", value / 100)
        # TODO: set volume

    def on_vsync_toggle(self, state):
        self.settings_manager.update_setting("vsync", state)
        # TODO: set vsync

    def on_ai_player_toggle(self, state):
        # TODO: set ai player
        self.settings_manager.update_setting("ai_player", state)

    def on_pacman_toggle(self, state):
        # TODO: set pacman on death
        self.settings_manager.update_setting("pacman", state)

    def on_debug_toggle(self, state):
        # TODO: set debug mode
        self.settings_manager.update_setting("debug", state)
