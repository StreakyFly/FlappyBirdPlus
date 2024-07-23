import os
import asyncio
import cProfile

from .modes import Mode
from .config import Config
from .utils import printc
from .flappybird import FlappyBird
from .ai.environments import EnvManager

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
        if Config.algorithm == 'DQN':
            from .ai.modelDQN import ModelDQN
            model = ModelDQN(env_type=Config.env_type)
        elif Config.algorithm == 'PPO':
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


def print_option_value_pair(option, value, color='default'):
    printc(option, color=color, end=' ')
    printc(value, color=color, styles=['bold'])


def print_config():
    print_option_value_pair("Mode:", Config.mode.name, color='green')
    print_option_value_pair("Environment type:", Config.env_type.name, color='blue')

    printc("Options:", color='yellow', end='')
    printc(" { ", end='')
    for key, value in Config.options.items():
        value_color = 'green' if value else 'red'
        printc("'", end='')
        printc(key, color='yellow', end='')
        printc("': ", end='')
        printc(value, color=value_color, end=', ')
    printc("}")

    print_option_value_pair("Model:", Config.algorithm, color='gray')


def validate_mode():
    if Config.mode not in Mode.__members__.values():
        raise ValueError(f"Invalid mode: {Config.mode}")

    print_config()


def execute_mode():
    if Config.options['headless']:
        os.environ["SDL_VIDEODRIVER"] = "dummy"

    if not Config.options['profile']:
        MODES[Config.mode]()
    else:
        cProfile.run(f"ModeExecutor.{MODES[Config.mode].__name__}()", sort='cumulative')
