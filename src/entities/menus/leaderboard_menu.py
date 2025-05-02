import threading
from datetime import datetime, timezone, timedelta
from enum import Enum

from src.utils import GameConfig, ResultsManager
from src.database import scores_service
from .menu import Menu
from .menu_manager import MenuManager
from .elements import Leaderboard, Tabs


class LeaderboardType(Enum):
    PERSONAL = "personal"
    GLOBAL = "global"


class LeaderboardMenu(Menu):
    def __init__(self, config: GameConfig, menu_manager: MenuManager):
        super().__init__(config, menu_manager, name="Leaderboard")
        self.leaderboard: Leaderboard = None
        self.results_manager: ResultsManager = None
        self.leaderboard_type = LeaderboardType.PERSONAL
        self.init_elements()

    def init_elements(self):
        # Personal leaderboard
        p_data, p_col_info = self.load_leaderboard(LeaderboardType.PERSONAL)
        personal_leaderboard = Leaderboard(config=self.config, width=476, height=423, data=p_data, column_info=p_col_info)
        self.leaderboard = personal_leaderboard
        self.load_leaderboard(LeaderboardType.PERSONAL, personal_leaderboard)  # fetch and update the personal leaderboard data in the background
        # Global leaderboard
        g_data, g_col_info = self.load_leaderboard(LeaderboardType.GLOBAL)
        global_leaderboard = Leaderboard(config=self.config, width=476, height=423, data=g_data, column_info=g_col_info)
        self.load_leaderboard(LeaderboardType.GLOBAL, global_leaderboard)  # fetch and update the global leaderboard data in the background

        tabs = Tabs(config=self.config, menu=self, tabs={
            "Personal": [
                {"element": personal_leaderboard, "x": 0, "y": 0, "align": "center"}
            ],
            "Global": [
                {"element": global_leaderboard, "x": 0, "y": 0, "align": "center"}
            ]
        })
        self.add_element(tabs, 0, 100, "center")

    def load_leaderboard(self, leaderboard_type: LeaderboardType, leaderboard: Leaderboard = None):
        self.leaderboard_type = leaderboard_type
        match leaderboard_type:
            case LeaderboardType.PERSONAL:
                return self.load_personal_leaderboard(leaderboard)
            case LeaderboardType.GLOBAL:
                return self.load_global_leaderboard(leaderboard)
            case _:
                raise ValueError(f"Unknown leaderboard type: {leaderboard_type}")

    def load_global_leaderboard(self, leaderboard: Leaderboard = None):
        column_info = {
            'rank': {'label': 'Rank', 'weight': 0.17},
            'username': {'label': 'Username', 'weight': 0.5},
            'score': {'label': 'Score', 'weight': 0.2},
            'timestamp': {'label': 'Date', 'weight': 0.3}
        }
        data = [{column: '...' for column in column_info.keys()}]

        if leaderboard is not None:
            def fetch_and_set_data():
                new_data = scores_service.get_scores(1000)  # TODO: implement pagination
                for index, entry in enumerate(new_data, start=1):
                    entry['rank'] = index
                leaderboard.set_data(self.format_data(new_data, '%d/%m/%y'), column_info)

            threading.Thread(target=fetch_and_set_data, daemon=True).start()

        return data, column_info

    def load_personal_leaderboard(self, leaderboard: Leaderboard = None):
        column_info = {
            'rank': {'label': 'Rank', 'weight': 0.17},
            'score': {'label': 'Score', 'weight': 0.32},
            'timestamp': {'label': 'Date', 'weight': 0.68}
        }
        data = [{column: '...' for column in column_info.keys()}]

        if leaderboard is not None:
            def fetch_and_set_data():
                if self.results_manager is None:
                    self.results_manager = ResultsManager()

                new_data = self.format_data(self.results_manager.get_results())
                for index, entry in enumerate(new_data, start=1):
                    entry['rank'] = index
                leaderboard.set_data(new_data, column_info)

            threading.Thread(target=fetch_and_set_data, daemon=True).start()

        return data, column_info

    @staticmethod
    def format_data(data, date_format: str = '%d/%m/%Y @ %H:%M'):
        local_offset = datetime.now().astimezone().utcoffset()

        for entry in data:
            timestamp = entry['timestamp']
            utc_time = datetime.strptime(timestamp, '%Y-%m-%dT%H:%M:%S.%f%z')
            local_time = utc_time + local_offset
            entry['timestamp'] = local_time.strftime(date_format)

        return data
