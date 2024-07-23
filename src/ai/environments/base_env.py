from src.flappybird import FlappyBird
from src.utils import GameState
from src.entities import PlayerMode


class BaseEnv(FlappyBird):
    def __init__(self):
        super().__init__()
        self.init_env()  # commented init_env() in gym_env.py and added it here

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

    @staticmethod
    def get_action_and_observation_space():
        """
        Get the action and observation space of the environment.
        :return: action space, observation space
        """
        NotImplementedError("set_action_and_observation_space() method must be implemented in the subclass")

    @staticmethod
    def get_observation_space_clip_modes():
        """
        Get the observation space clipping modes for each part of the observation space.

        Keys:
        - if the observation space is a Box space, the key should be 'box'
        - if the observation space is a Dict space, the keys should be the same as the keys in the Dict space
        Modes (values):
        -1: raise an error if the observation is out of bounds;
        0: do nothing;
        1: clip the observation to the valid range of the observation space;

        :return: a dictionary containing the clipping modes for each part of the observation space
        """
        NotImplementedError("get_observation_space_clip_modes() method must be implemented in the subclass")

    def perform_step(self, action: int | list[int]):
        """
        Step through the game one frame at a time with the given action.
        :param action: action(s) the agent took
        :return: observation, reward, terminated, truncated
        """
        NotImplementedError("perform_step() method must be implemented in the subclass")

    def get_observation(self):
        """
        Get the current observation of the game.
        :return: game observation
        """
        NotImplementedError("get_observation() method must be implemented in the subclass")

    def get_action_masks(self):
        """
        Get the action masks for the current game state.
        Each mask corresponds to whether an action is feasible (1) or not (0).

        This method is required ONLY if requires_action_masking is True.
        :return: np.ndarray: A numpy array of shape (num_actions,) where each element is either 0 or 1.
        """
        NotImplementedError("get_action_masks() method must be implemented in the subclass")

    def calculate_reward(self, *args):
        """
        Calculate the reward for the current game state.
        :param args: depends on the environment
        :return: a number representing the reward
        """
        NotImplementedError("calculate_reward() method must be implemented in the subclass")
