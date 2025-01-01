from .file_manager import FileManager


class SettingsManager(FileManager):
    def __init__(self, directory="data", settings_file="settings.json"):
        super().__init__(directory)
        self.settings_file = settings_file
        self.default_settings = {
            "volume": 0.5,
            "vsync": False,
        }
        self._initialize_settings()

    def _initialize_settings(self):
        """ Initialize settings if they do not exist. """
        if not self.file_exists(self.settings_file):
            self.save_settings(self.default_settings)

    def load_settings(self):
        """ Load settings from the settings file. """
        settings = self.load_file(self.settings_file, default=self.default_settings)

        # Validate the settings
        for key, value in self.default_settings.items():
            if key not in settings:
                settings[key] = value

        return settings

    def save_settings(self, settings):
        """ Save settings to the settings file. """
        self.save_file(self.settings_file, settings)

    def reset_settings(self):
        """ Reset settings to default. """
        self.save_settings(self.default_settings)
        return self.default_settings
