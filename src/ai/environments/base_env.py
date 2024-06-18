from ...flappybird import FlappyBird

from ...utils import GameState
from ...entities import PlayerMode


class BaseEnv(FlappyBird):
    def __init__(self):
        super().__init__()

    def init_env(self) -> None:
        """
        Initialize the game environment.
        :return: nothing
        """
        self.reset()
        self.gsm.set_state(GameState.PLAY)
        self.player.set_mode(PlayerMode.NORMAL)

    def reset_env(self):
        """
        Reset the game environment.
        :return: nothing
        """
        self.reset()
        self.gsm.set_state(GameState.PLAY)
        self.player.set_mode(PlayerMode.NORMAL)

    def get_action_and_observation_space(self):
        NotImplementedError("set_action_and_observation_space() method must be implemented in the subclass")

    def perform_step(self, action: int | list[int]):
        """
        Step through the game one frame at a time with the given action.
        :param action: action(s) the agent took
        :return: observation, reward, terminated, truncated
        """
        NotImplementedError("step() method must be implemented in the subclass")

    def get_state(self):
        """
        Get the current state of the game.
        :return: game state
        """
        NotImplementedError("get_state() method must be implemented in the subclass")

    def calculate_reward(self, *args):
        """
        Calculate the reward for the current game state.
        :param args: depends on the environment
        :return: a number representing the reward
        """
        NotImplementedError("calculate_reward() method must be implemented in the subclass")
