import os
import asyncio
import cProfile

from modes import Mode
from config import config
from src.utils import printc
from src.flappybird import FlappyBird
from src.ai.env_manager import EnvManager


class ModeExecutor:
    @staticmethod
    def play_mode():
        asyncio.run(FlappyBird().start())

    @staticmethod
    def test_env_mode():
        EnvManager(env_type=config['env_type']).test_env()

    @staticmethod
    def train_mode():
        config['model'].set_env_type(config['env_type'])
        config['model'].train()

    @staticmethod
    def continue_training_mode():
        config['model'].set_env_type(config['env_type'])
        config['model'].continue_training()

    @staticmethod
    def run_model_mode():
        config['model'].set_env_type(config['env_type'])
        config['model'].run()

    @staticmethod
    def evaluate_model_mode():
        config['model'].set_env_type(config['env_type'])
        config['model'].evaluate()


MODES = {
    Mode.PLAY: ModeExecutor.play_mode,
    Mode.TEST_ENV: ModeExecutor.test_env_mode,
    Mode.TRAIN: ModeExecutor.train_mode,
    Mode.CONTINUE_TRAINING: ModeExecutor.continue_training_mode,
    Mode.RUN_MODEL: ModeExecutor.run_model_mode,
    Mode.EVALUATE_MODEL: ModeExecutor.evaluate_model_mode,
}


def print_config():
    printc(f"Environment type: {config['env_type']}", color='blue')
    printc(f"Options: {config['options']}", color='green')
    printc(f"Model: {config['model'].__name__}", color='blue')


def validate_mode():
    if config['mode'] in Mode.__members__.values():
        printc(f"Mode: {config['mode']}", color='green')
    else:
        printc(f"Invalid mode: {config['mode']}", color='red')

    print_config()


def execute_mode():
    if config['options']['headless']:
        os.environ["SDL_VIDEODRIVER"] = "dummy"

    if not config['options']['profile']:
        MODES[config['mode']]()
    else:
        cProfile.run(f"ModeExecutor.{MODES[config['mode']].__name__}()", sort='cumulative')
