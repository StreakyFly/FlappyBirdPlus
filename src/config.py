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
    mode: Mode = Mode.RUN_MODEL  # <-- change the mode here
    algorithm: Literal['PPO', 'DQN'] = 'PPO'  # <-- change the algorithm here (PPO is the only one fully supported)
    env_type: EnvType = EnvType.ENEMY_CLOUDSKIMMER  # <-- change environment type here
    env_variant: EnvVariant = EnvVariant.SIMPLE  # <-- change environment variant here (doesn't work for Mode.PLAY)
    run_id: Optional[str] = "run_20250530_131801" #None  # "run_test"  # <-- change the run id here (can/should be None for some modes)
    seed: Optional[int] = 42  # <-- change the training seed here (can be None; used only by the PPO algorithm, not the game environment)
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
                printc("CONFIG WARNING! Headless mode is enabled but audio is not muted.", color="orange")
            if cls.debug:
                printc("CONFIG WARNING! Headless mode is enabled along with debug mode.", color="orange")
            if cls.fps_cap > 0:
                printc("CONFIG WARNING! Headless mode is enabled but FPS is capped. Use 0 for no FPS cap.", color="orange")
            if cls.mode == Mode.RUN_MODEL:
                printc("CONFIG WARNING! Headless mode is enabled but mode is set to Mode.RUN_MODEL.", color="orange")
        if cls.env_variant != EnvVariant.MAIN and cls.mode == Mode.PLAY:
            printc("CONFIG WARNING! Mode.PLAY will NOT take the env_variant into account. EnvVariant.MAIN will be used instead.", color="orange")
        if cls.algorithm == 'PPO' and cls.run_id is None and cls.mode in [Mode.CONTINUE_TRAINING, Mode.EVALUATE_MODEL, Mode.RUN_MODEL]:
            raise ValueError("The selected mode requires a run_id.")
        if cls.mode == Mode.TRAIN and cls.run_id is not None:
            raise ValueError("Nuh-uh! Mode is set to Mode.TRAIN, but run_id is not None. "
                             "This will overwrite the existing model with specified run_id (if it exists) "
                             "- you most likely don't want that. If you do, manually delete the existing model.")


Config.verify_config()
