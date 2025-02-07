import pygame

from src.utils import GameConfig
from .menu import Menu
from .menu_manager import MenuManager
from .elements import Slider, Toggle, TextInput, Tabs


class SettingsMenu(Menu):
    def __init__(self, config: GameConfig, menu_manager: MenuManager):
        super().__init__(config, menu_manager, name="Settings")
        self.settings_manager = config.settings_manager
        self.init_elements()

    def init_elements(self):
        username_input = TextInput(config=self.config, label="Username", width=420, initial_text=self.settings_manager.get_setting("username"), max_length=30, on_text_change=self.on_text_change)
        volume_slider = Slider(config=self.config, label="Volume", initial_value=self.settings_manager.get_setting("volume") * 100, on_slide=self.on_volume_slide)
        vsync_toggle = Toggle(config=self.config, label="V-sync", initial_state=self.settings_manager.get_setting("vsync"), on_toggle=self.on_vsync_toggle)
        ai_player_toggle = Toggle(config=self.config, label="AI Player", initial_state=self.settings_manager.get_setting("ai_player"), on_toggle=self.on_ai_player_toggle)
        pacman_toggle = Toggle(config=self.config, label="Pacman on death", initial_state=self.settings_manager.get_setting("pacman"), on_toggle=self.on_pacman_toggle)
        debug_toggle = Toggle(config=self.config, label="Debug mode", initial_state=self.settings_manager.get_setting("debug"), on_toggle=self.on_debug_toggle)
        tabs = Tabs(config=self.config, menu=self, tabs={
                        "General": [
                            {"element": username_input, "x": 0, "y": 80, "align": "left"},
                            {"element": volume_slider, "x": 0, "y": 215, "align": "left"},
                            {"element": vsync_toggle, "x": 0, "y": 320, "align": "left"},
                        ],
                        "Gameplay": [
                            {"element": ai_player_toggle, "x": 0, "y": 80, "align": "left"},
                            {"element": pacman_toggle, "x": 0, "y": 200, "align": "left"},
                            {"element": debug_toggle, "x": 0, "y": 320, "align": "left"},
                        ],
                    })
        self.add_element(tabs, 0, 100, "center")

    def on_text_change(self, text):
        self.settings_manager.update_setting("username", text.strip() or self.settings_manager.get_random_username())

    def on_volume_slide(self, value):
        volume = pygame.math.clamp(value, 0, 100) / 100
        self.settings_manager.update_setting("volume", volume)
        self.config.sounds.set_global_volume(volume)

    def on_vsync_toggle(self, state):
        self.settings_manager.update_setting("vsync", state)
        # TODO: set vsync

    def on_ai_player_toggle(self, state):
        self.settings_manager.update_setting("ai_player", state)
        self.config.human_player = not state

    def on_pacman_toggle(self, state):
        self.settings_manager.update_setting("pacman", state)
        self.config.pacman = state

    def on_debug_toggle(self, state):
        self.settings_manager.update_setting("debug", state)
        self.config.debug = state
