from .utils import printc

from .modes import Mode
from .ai.environments.env_types import EnvType


class Config:
    fps_cap = 30  # <-- change the FPS cap here; default = 30; no cap = 0 or a negative value
    debug = False  # <-- change if you want to enable debug mode
    algorithm = 'PPO'  # <-- change the algorithm here (DQN or PPO)
    mode = Mode.RUN_MODEL  # <-- change the mode here
    env_type = EnvType.ENEMY_CLOUDSKIMMER  # <-- change environment type here
    run_id = "run_20240716_112512"  # <-- change the run id here (can be None for some modes)

    options = {
        'headless': False,  # run pygame in headless mode to increase performance
        'mute': True,  # mute the audio (slight performance boost)
        'profile': False,  # profile the code execution
    }

    @classmethod
    def verify_config(cls):
        if cls.algorithm not in ['DQN', 'PPO']:
            raise ValueError(f"Invalid model: {cls.algorithm}")
        if cls.options['headless']:
            if not cls.options['mute']:
                printc("CONFIG WARNING! Headless mode is enabled but audio is not muted.", color="orange")
            if cls.debug:
                printc("CONFIG WARNING! Headless mode is enabled along with debug mode.", color="orange")
            if cls.fps_cap > 0:
                printc("CONFIG WARNING! Headless mode is enabled but FPS is capped. Use 0 for no FPS cap.", color="orange")
            if cls.mode == Mode.RUN_MODEL:
                printc("CONFIG WARNING! Headless mode is enabled but mode is set to run the model.", color="orange")
        if cls.algorithm == 'PPO' and cls.run_id is None and cls.mode in [Mode.CONTINUE_TRAINING, Mode.EVALUATE_MODEL, Mode.RUN_MODEL]:
            raise ValueError("The selected mode requires a run_id.")
        if cls.mode == Mode.TRAIN and cls.run_id is not None:
            raise ValueError("Nuh-uh! Mode is set to Mode.TRAIN, but run_id is not None. "
                             "This will overwrite the existing model with specified run_id (if it exists) "
                             "- you most likely don't want that. If you do, manually delete the existing model.")


Config.verify_config()
