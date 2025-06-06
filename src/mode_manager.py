import asyncio
import cProfile
import os

from .ai.environments import EnvManager
from .config import Config
from .flappybird import FlappyBird
from .modes import Mode
from .utils import printc

"""  # noqa: E265
Very simple control flow diagram:
main -> mode_manager -> FlappyBird().start()
                     -> EnvManager().test_env() -> GymEnv -> FlappyBird().init_env()
                     -> modelPPO -> EnvManager().get_env() -> GymEnv -> FlappyBird().init_env()
                     
###################################################################################################
Random seed needs to be set for all modes at the right time!
Loading a trained model with Stable Baselines3 sets the seed to the one used during training.
If we want to override it, we must do so **after** loading the model!
This is currently handled in the following files (at the time of writing...):
 - modelPPO.py, in the ModelPPO class in _load_model() method, after loading the model
 - base_controller.py, in the BaseModelController class in __init__() method, after loading the model
 - gym_env.py, in the GymEnv class in reset() method

For Mode.PLAY, the seed is not set directly in the FlappyBird() class, but is set when
controllers are initialized (by base_controller.py, as previously mentioned).
If you don't call init_model_controllers() in FlappyBird(), the seed will not be set for Mode.PLAY.
###################################################################################################
"""


class ModeExecutor:
    @staticmethod
    def play():
        # asyncio.run(FlappyBird().start())
        game_instance = FlappyBird()
        game_instance.init_model_controllers(human_player=Config.human_player)  # TODO: comment when testing non-AI things to speed up load time
        asyncio.run(game_instance.start())

    @staticmethod
    def test_env():
        EnvManager(env_type=Config.env_type, env_variant=Config.env_variant).test_env()

    @staticmethod
    def train():
        ModeExecutor.init_model().train()

    @staticmethod
    def continue_training():
        ModeExecutor.init_model().continue_training()

    @staticmethod
    def run_model():
        ModeExecutor.init_model().run()

    @staticmethod
    def evaluate_model():
        ModeExecutor.init_model().evaluate()

    @staticmethod
    def init_model():
        if Config.algorithm == 'DQN':
            from .ai.modelDQN import ModelDQN
            model = ModelDQN(env_type=Config.env_type)
        elif Config.algorithm == 'PPO':
            from .ai.modelPPO import ModelPPO
            model = ModelPPO(env_type=Config.env_type, env_variant=Config.env_variant, run_id=Config.run_id)
        else:
            raise ValueError(f"Invalid algorithm: {Config.algorithm}")

        return model


MODES = {
    Mode.PLAY: ModeExecutor.play,
    Mode.TEST_ENV: ModeExecutor.test_env,
    Mode.TRAIN: ModeExecutor.train,
    Mode.CONTINUE_TRAINING: ModeExecutor.continue_training,
    Mode.RUN_MODEL: ModeExecutor.run_model,
    Mode.EVALUATE_MODEL: ModeExecutor.evaluate_model,
}


def print_option_value_pair(option, value, comment=None, color='default'):
    printc(option, color=color, end=' ')
    printc(value, color=color, styles=['bold'], end=' ')
    if comment is not None:
        printc(comment, color='gray')
    else:
        print()


def print_config():
    print()
    print_option_value_pair("Mode:", Config.mode.name, color='green')
    if Config.mode == Mode.PLAY:
        print_option_value_pair("Environment type:", Config.env_type.name, comment="(not used)", color='gray')
        print_option_value_pair("Environment variant:", Config.env_variant.name, comment="(not used)", color='gray')
    else:
        print_option_value_pair("Environment type:", Config.env_type.name, color='blue')
        print_option_value_pair("Environment variant:", Config.env_variant.name, color='cyan')

    printc("Options:", color='yellow', end='')
    printc(" { ", end='')
    for key, value in Config.options.items():
        value_color = 'green' if value else 'red'
        printc("'", end='')
        printc(key, color='yellow', end='')
        printc("': ", end='')
        printc(value, color=value_color, end=', ')
    printc("}")

    if Config.mode in [Mode.TRAIN, Mode.CONTINUE_TRAINING]:
        print_option_value_pair("Model:", Config.algorithm, color='pink')
    else:
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
