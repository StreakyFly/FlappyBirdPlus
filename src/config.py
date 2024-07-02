from .utils import printc

from .modes import Mode
from .ai.environments.env_types import EnvType


class Config:
    fps_cap = 30  # <-- change the FPS cap here; default = 30; 0 = uhh, it fucks up stuff, don't use it, do 9999 instead
    debug = False  # <-- change if you want to enable debug mode
    model = 'PPO'  # <-- change the model here (DQN or PPO)
    mode = Mode.PLAY  # <-- change the mode here
    env_type = EnvType.ENEMY_CLOUDSKIMMER  # <-- change environment type here
    run_id = None #"run_20240617_182959"  # <-- change the run id here (can be None in some cases)

    options = {
        'headless': False,  # run pygame in headless mode to increase performance
        'mute': True,  # mute the audio (slight performance boost)
        'profile': False,  # profile the code
    }

    # TODO should we warn user if headless is enabled but fps cap is low, like 30?

    @classmethod
    def verify_config(cls):
        if cls.model not in ['DQN', 'PPO']:
            raise ValueError(f"Invalid model: {cls.model}")
        if cls.options['headless'] and not cls.options['mute']:
            printc("WARNING! Headless mode is enabled but audio is not muted.", color="yellow")
        if cls.model == 'PPO' and cls.run_id is None and cls.mode not in [Mode.TRAIN, Mode.PLAY, Mode.TEST_ENV]:
            raise ValueError("The selected mode requires a run_id.")
        if cls.mode == Mode.TRAIN and cls.run_id is not None:
            raise ValueError("Nuh-uh! Mode is set to Mode.TRAIN, but run_id is not None."
                             " This will overwrite the existing model with specified run_id (if it exists)"
                             " - you most likely don't want that. If you do, manually delete the existing model.")


Config.verify_config()
