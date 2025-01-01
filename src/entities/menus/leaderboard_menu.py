from datetime import datetime
import threading

from src.utils import GameConfig
from src.database import scores_service
from .menu import Menu
from .menu_manager import MenuManager
from .elements import Leaderboard


class LeaderboardMenu(Menu):
    def __init__(self, config: GameConfig, menu_manager: MenuManager):
        super().__init__(config, menu_manager, name="Leaderboard")
        self.leaderboard: Leaderboard = None
        self.init_elements()

    def init_elements(self):
        # TODO: implement a proper loading element
        self.leaderboard = Leaderboard(config=self.config, width=420, height=440,
                                       data=self.load_personal_leaderboard(),
                                       column_info={
                                           'score': { 'label': 'Score', 'weight': 0.32 },
                                           'timestamp': { 'label': 'Date', 'weight': 0.68 }
                                           }
                                       )
        self.add_element(self.leaderboard, 0, 30)

    def load_global_leaderboard(self):
        def fetch_data():
            data = scores_service.get_scores()
            self.leaderboard.set_data(self.format_data(data))
        threading.Thread(target=fetch_data, daemon=True).start()
        return [{'score': '...', 'timestamp': '...'}]

    def load_personal_leaderboard(self):
        # TODO: load leaderboard data from data/leaderboard.json
        return self.format_data([
            {'score': 987, 'timestamp': '2024-11-28T17:23:02.574329+00:00'},
            {'score': 250, 'timestamp': '2024-12-05T10:47:50.516017+00:00'},
            {'score': 200, 'timestamp': '2024-11-28T17:18:30.926578+00:00'},
            {'score': 190, 'timestamp': '2024-11-28T17:19:06.914695+00:00'},
            {'score': 99, 'timestamp': '2024-12-05T21:49:18.512342+00:00'},
            {'score': 69, 'timestamp': '2024-12-05T10:36:32.188202+00:00'},
            {'score': 50, 'timestamp': '2024-12-05T21:42:48.88632+00:00'},
            {'score': 29, 'timestamp': '2024-12-05T10:55:44.307772+00:00'},
            {'score': 25, 'timestamp': '2024-12-05T21:48:38.829994+00:00'},
            {'score': 20, 'timestamp': '2024-12-05T22:26:09.098878+00:00'},
            {'score': 20, 'timestamp': '2024-12-05T10:55:38.186221+00:00'},
            {'score': 5, 'timestamp': '2024-11-28T17:20:36.099627+00:00'}
        ])

    @staticmethod
    def format_data(data):
        for entry in data:
            timestamp = entry['timestamp']
            entry['timestamp'] = datetime.strptime(timestamp, '%Y-%m-%dT%H:%M:%S.%f%z').strftime('%d-%m-%Y @ %H:%M')
        return data
