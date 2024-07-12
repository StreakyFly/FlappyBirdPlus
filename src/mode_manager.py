import os
import asyncio
import cProfile

from .modes import Mode
from .config import Config
from .utils import printc
from .flappybird import FlappyBird
from .ai.env_manager import EnvManager

"""  # noqa: E265
Very simple control flow diagram:
main -> mode_manager -> FlappyBird().start()
                     -> EnvManager().test_env() -> GymEnv -> FlappyBird().init_env()
                     -> agentDQN -> EnvManager().get_env() -> GymEnv -> FlappyBird().init_env()
"""


class ModeExecutor:
    @staticmethod
    def play_mode():
        asyncio.run(FlappyBird().start())

    @staticmethod
    def test_env_mode():
        EnvManager(env_type=Config.env_type).test_env()

    @staticmethod
    def train_mode():
        ModeExecutor.init_model().train()

    @staticmethod
    def continue_training_mode():
        ModeExecutor.init_model().continue_training()

    @staticmethod
    def run_model_mode():
        ModeExecutor.init_model().run()

    @staticmethod
    def evaluate_model_mode():
        ModeExecutor.init_model().evaluate()

    @staticmethod
    def init_model():
        model = None
        if Config.model == 'DQN':
            from .ai.modelDQN import ModelDQN
            model = ModelDQN(env_type=Config.env_type)
        elif Config.model == 'PPO':
            from .ai.modelPPO import ModelPPO
            model = ModelPPO(env_type=Config.env_type, run_id=Config.run_id)

        return model


MODES = {
    Mode.PLAY: ModeExecutor.play_mode,
    Mode.TEST_ENV: ModeExecutor.test_env_mode,
    Mode.TRAIN: ModeExecutor.train_mode,
    Mode.CONTINUE_TRAINING: ModeExecutor.continue_training_mode,
    Mode.RUN_MODEL: ModeExecutor.run_model_mode,
    Mode.EVALUATE_MODEL: ModeExecutor.evaluate_model_mode,
}


def print_config():
    printc(f"Environment type: {Config.env_type}", color='blue')
    printc(f"Options: {Config.options}", color='green')
    printc(f"Model: {Config.model}", color='blue')


def validate_mode():
    if Config.mode in Mode.__members__.values():
        printc(f"Mode: {Config.mode}", color='green')
    else:
        printc(f"Invalid mode: {Config.mode}", color='red')

    print_config()


def execute_mode():
    if Config.options['headless']:
        os.environ["SDL_VIDEODRIVER"] = "dummy"

    if not Config.options['profile']:
        MODES[Config.mode]()
    else:
        cProfile.run(f"ModeExecutor.{MODES[Config.mode].__name__}()", sort='cumulative')
