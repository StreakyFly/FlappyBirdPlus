from datetime import datetime
from enum import Enum
import threading

from src.utils import GameConfig, ResultsManager
from src.database import scores_service
from .menu import Menu
from .menu_manager import MenuManager
from .elements import Leaderboard


# TODO: add option to switch between personal and global leaderboard

class LeaderboardType(Enum):
    PERSONAL = "personal"
    GLOBAL = "global"


class LeaderboardMenu(Menu):
    def __init__(self, config: GameConfig, menu_manager: MenuManager):
        super().__init__(config, menu_manager, name="Leaderboard")
        self.leaderboard: Leaderboard = None
        self.results_manager = ResultsManager()
        self.leaderboard_type = LeaderboardType.PERSONAL  # TODO: store this in settings.json
        self.init_elements()

    def init_elements(self):
        # TODO: implement a proper loading element
        data, column_info = self.load_leaderboard(self.leaderboard_type)
        self.leaderboard = Leaderboard(config=self.config, width=420, height=440, data=data, column_info=column_info)
        self.add_element(self.leaderboard, 0, 25)

    def load_leaderboard(self, leaderboard_type: LeaderboardType):
        self.leaderboard_type = leaderboard_type
        if self.leaderboard is not None:
            self.leaderboard.set_data([])  # TODO: instead of clearing the data, show the loading element overlay until the new data is loaded & set
        match leaderboard_type:
            case LeaderboardType.PERSONAL:
                return self.load_personal_leaderboard()
            case LeaderboardType.GLOBAL:
                return self.load_global_leaderboard()
            case _:
                raise ValueError(f"Unknown leaderboard type: {leaderboard_type}")

    def load_global_leaderboard(self):
        column_info = {
            'username': {'label': 'Username', 'weight': 0.5},
            'score': {'label': 'Score', 'weight': 0.2},
            'timestamp': {'label': 'Date', 'weight': 0.3}
        }
        def fetch_data():
            data = scores_service.get_scores()
            self.leaderboard.set_data(self.format_data(data, '%d/%m/%y'), column_info)
        threading.Thread(target=fetch_data, daemon=True).start()
        return [{column: '...' for column in column_info.keys()}], column_info

    def load_personal_leaderboard(self):
        data = self.format_data(self.results_manager.results)
        column_info = {
            'score': {'label': 'Score', 'weight': 0.32},
            'timestamp': {'label': 'Date', 'weight': 0.68}
        }
        return data, column_info

    @staticmethod
    def format_data(data, date_format: str = '%d/%m/%Y @ %H:%M'):
        for entry in data:
            timestamp = entry['timestamp']
            entry['timestamp'] = datetime.strptime(timestamp, '%Y-%m-%dT%H:%M:%S.%f%z').strftime(date_format)
        return data
