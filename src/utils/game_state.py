from enum import Enum


class GameState(Enum):
    START = 'start'
    PLAY = 'play'
    END = 'end'


class GameStateManager:
    def __init__(self):
        self.game_state = GameState.START

    def set_state(self, state):
        if state in GameState:
            self.game_state = state
        else:
            print(f"Invalid game state: {state}")

    def get_state(self):
        return self.game_state
