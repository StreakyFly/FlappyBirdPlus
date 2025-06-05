from typing import Literal
from typing import Optional

from .ai.environments import EnvType
from .ai.environments.env_types import EnvVariant
from .modes import Mode
from .utils import printc, SettingsManager


class Config:
    settings_manager = SettingsManager()  # load settings
    fps_cap: int = 30  # <-- change the FPS cap here; default = 30; no cap = 0 or a negative value
    num_cores: int = 8  # <-- change the number of cores to use during training (more != faster training)
    debug: bool = settings_manager.get_setting('debug')  # <-- toggle debug mode
    mode: Mode = Mode.TEST_ENV  # <-- change the mode here
    algorithm: Literal['PPO', 'DQN'] = 'PPO'  # <-- change the algorithm here (PPO is the only one fully supported)
    env_type: EnvType = EnvType.ENEMY_CLOUDSKIMMER  # <-- change environment type here
    env_variant: EnvVariant = EnvVariant.STEP3  # <-- change environment variant here (doesn't work for Mode.PLAY)
    run_id: Optional[str] = None  # "run_test"  # <-- change the run id here (can/should be None for some modes)
    seed: Optional[int] = 42  # <-- None = set dynamic random seed; non-negative = fixed seed; used by the PPO algorithm and game environments
    handle_seed: bool = True  # <-- toggle if you want to handle the seed yourself (use False for Mode.TRAIN and in specific situations for some other modes)
    human_player: bool = not settings_manager.get_setting('ai_player')  # <-- toggle if you want to play the game yourself (only works for Mode.PLAY)
    save_results: bool = True  # <-- toggle if you want to save the results to file & database

    options = {
        'headless': False,  # run pygame in headless mode to increase performance
        'mute': False,  # mute the audio (slight performance boost)
        'profile': False,  # profile the code execution
    }

    @classmethod
    def verify_config(cls):
        if cls.options['headless']:
            if not cls.options['mute']:
                cls.printcw("Headless mode is enabled but audio is not muted.")
            if cls.debug:
                cls.printcw("Headless mode is enabled along with debug mode.")
            if cls.fps_cap > 0:
                cls.printcw("Headless mode is enabled but FPS is capped. Use 0 for no FPS cap.")
            if cls.mode == Mode.RUN_MODEL:
                cls.printcw("Headless mode is enabled but mode is set to Mode.RUN_MODEL.")
        if cls.env_variant != EnvVariant.MAIN and cls.mode == Mode.PLAY:
            cls.printcw("Mode.PLAY will NOT take the env_variant into account. EnvVariant.MAIN will be used instead.")
        if cls.algorithm == 'PPO' and cls.run_id is None and cls.mode in [Mode.CONTINUE_TRAINING, Mode.EVALUATE_MODEL, Mode.RUN_MODEL]:
            raise ValueError("The selected mode requires a run_id.")
        if cls.mode == Mode.TRAIN and cls.run_id is not None:
            raise ValueError("Nuh-uh! Mode is set to Mode.TRAIN, but run_id is not None. "
                             "This will overwrite the existing model with specified run_id (if it exists) "
                             "- you most likely don't want that. If you do, manually delete the existing model.")

        # Verify seed
        if cls.seed is not None and cls.seed < 0:
            raise ValueError(f"Seed is set to: '{cls.seed}'. What the heck do you want me to do with that?")
        elif cls.mode == Mode.PLAY:
            if not cls.handle_seed:
                cls.printcw("Mode is set to Mode.PLAY, but handle_seed is set to False. This means Stable Baselines3 "
                            "will likely use a fixed random seed (the one used during training), making runs upon restart identical. "
                            "You most likely don't want this. Setting handle_seed to True is recommended.", color='red')
            elif cls.handle_seed and cls.seed is not None:
                cls.printcw("Mode is set to Mode.PLAY, but seed is set to a fixed value. "
                            "This means that each time you run the game, you'll get the exact same environment. "
                            "You most likely don't want this. Setting the seed to None is recommended.", color='red')
        elif cls.mode == Mode.TRAIN and cls.handle_seed:
            cls.printcw("Mode is set to Mode.TRAIN, but handle_seed is set to True. This means that the incremental "
                        "seeds given to the environments by Stable Baselines3 will not be respected — they will be overridden with "
                        "currently set seed (the one specified in Config.seed), which means all environments will be identical. "
                        "You most likely don't want this. Setting handle_seed to False is recommended.", color='red')
        elif cls.mode == Mode.CONTINUE_TRAINING and cls.handle_seed:
            cls.printcw("Mode is set to Mode.CONTINUE_TRAINING, but handle_seed is set to a True, which does not respect "
                        "the seed that was set by Stable Baselines3 (seed used during training) — that seed will be "
                        "overridden with currently set seed (the one specified in Config.seed). "
                        "Unless you have a specific reason for this, set handle_seed to False.")
        elif cls.mode == Mode.RUN_MODEL:
            if not cls.handle_seed:
                cls.printcw("Mode is set to Mode.RUN_MODEL, but handle_seed is set to False. This means Stable Baselines3 "
                            "will likely use a fixed random seed (the one used during training), making runs upon restart identical. "
                            "Unless you have a specific reason for this, set handle_seed to True.")
            elif cls.handle_seed and cls.seed is not None:
                cls.printcw("Mode is set to Mode.RUN_MODEL, but seed is set to a fixed value. "
                            "This means that each time you run the game, you'll get the exact same environment. "
                            "Unless you have a specific reason for this, set seed to None.")
        elif cls.mode == Mode.EVALUATE_MODEL:
            if not cls.handle_seed:
                cls.printcw("Mode is set to Mode.EVALUATE_MODEL, but handle_seed is set to False. "
                            "This means that the same seed will likely be used as in training, which will lead to biased results. "
                            "Unless you have a specific reason for this, set handle_seed to True.")
            elif cls.handle_seed and cls.seed is not None:
                cls.printcw("Mode is set to Mode.EVALUATE_MODEL, but seed is set to a fixed value (which could also possibly match the seed used during training). "
                            "This means that each time you run the evaluation, you'll get the exact same environment. "
                            "Unless you have a specific reason for this, set seed to None.")

    @staticmethod
    def printcw(message: str, color: str = 'orange') -> None:
        printc("[CONFIG WARN]", color=color, styles=['bold'], end=' ')
        printc(message, color=color)


Config.verify_config()
