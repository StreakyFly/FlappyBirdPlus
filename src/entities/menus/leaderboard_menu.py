from datetime import datetime
from enum import Enum
import threading

from src.utils import GameConfig, ResultsManager
from src.database import scores_service
from .menu import Menu
from .menu_manager import MenuManager
from .elements import Leaderboard, Tabs


# TODO: add option to switch between personal and global leaderboard

class LeaderboardType(Enum):
    PERSONAL = "personal"
    GLOBAL = "global"


class LeaderboardMenu(Menu):
    def __init__(self, config: GameConfig, menu_manager: MenuManager):
        super().__init__(config, menu_manager, name="Leaderboard")
        self.leaderboard: Leaderboard = None
        self.results_manager = ResultsManager()
        self.leaderboard_type = LeaderboardType.PERSONAL
        self.init_elements()

    def init_elements(self):
        # TODO: implement a proper loading element
        p_data, p_col_info = self.load_leaderboard(LeaderboardType.PERSONAL)
        personal_leaderboard = Leaderboard(config=self.config, width=476, height=423, data=p_data, column_info=p_col_info)
        g_data, g_col_info = self.load_leaderboard(LeaderboardType.GLOBAL)
        global_leaderboard = Leaderboard(config=self.config, width=476, height=423, data=g_data, column_info=g_col_info)
        self.load_leaderboard(LeaderboardType.GLOBAL, global_leaderboard)  # fetch and update the global leaderboard data in the background
        tabs = Tabs(config=self.config, menu=self, tabs={
            "Personal": [
                {"element": personal_leaderboard, "x": 0, "y": 25, "align": "center"}
            ],
            "Global": [
                {"element": global_leaderboard, "x": 0, "y": 25, "align": "center"}
            ]
        })
        self.leaderboard = personal_leaderboard
        self.add_element(tabs, 0, 100, "center")

    def load_leaderboard(self, leaderboard_type: LeaderboardType, leaderboard: Leaderboard = None):
        self.leaderboard_type = leaderboard_type
        if self.leaderboard is not None:
            self.leaderboard.set_data([])  # TODO: instead of clearing the data, show the loading element overlay until the new data is loaded & set
        match leaderboard_type:
            case LeaderboardType.PERSONAL:
                return self.load_personal_leaderboard()
            case LeaderboardType.GLOBAL:
                return self.load_global_leaderboard(leaderboard)
            case _:
                raise ValueError(f"Unknown leaderboard type: {leaderboard_type}")

    def load_global_leaderboard(self, leaderboard: Leaderboard = None):
        column_info = {
            'username': {'label': 'Username', 'weight': 0.5},
            'score': {'label': 'Score', 'weight': 0.2},
            'timestamp': {'label': 'Date', 'weight': 0.3}
        }
        data = [{column: '...' for column in column_info.keys()}]

        def fetch_and_set_data():
            new_data = scores_service.get_scores()
            leaderboard.set_data(self.format_data(new_data, '%d/%m/%y'), column_info)

        if leaderboard is not None:
            threading.Thread(target=fetch_and_set_data, daemon=True).start()

        return data, column_info

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
            # TODO: format date based on the user's locale
            # entry['timestamp'] = datetime.fromisoformat(entry['timestamp']).strftime(date_format)
            timestamp = entry['timestamp']
            entry['timestamp'] = datetime.strptime(timestamp, '%Y-%m-%dT%H:%M:%S.%f%z').strftime(date_format)

        return data
