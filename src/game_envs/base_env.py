from ..flappybird import FlappyBird


class BaseEnv(FlappyBird):
    def __init__(self):
        super().__init__()

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
        :return: depending on the environment
        """
        NotImplementedError("calculate_reward() method must be implemented in the subclass")
