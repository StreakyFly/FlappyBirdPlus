from .utils import printc

from .modes import Mode
from .ai.environments.env_types import EnvType


class Config:
    FPS_CAP = 30  # <-- change the FPS cap here; default = 30; 0 = uhh, it fucks up stuff, don't use it, do 9999 instead
    model = 'PPO'  # <-- change the model here (DQN or PPO)
    env_type = EnvType.ENEMY_CLOUDSKIMMER  # <-- change environment type here
    mode = Mode.TEST_ENV  # <-- change the mode here
    run_id = None #"run_20240617_182959"  # <-- change the run id here (can be None when playing or training a new model)

    options = {
        'headless': False,  # run pygame in headless mode to increase performance
        'mute': True,  # mute the audio (slight performance boost)
        'profile': False,  # profile the code
    }

    @classmethod
    def verify_config(cls):
        if cls.model not in ['DQN', 'PPO']:
            raise ValueError(f"Invalid model: {cls.model}")
        if cls.options['headless'] and not cls.options['mute']:
            printc("WARNING! Headless mode is enabled but audio is not muted.", color="yellow")
        if cls.model == 'PPO' and cls.run_id is None and cls.mode not in [Mode.TRAIN, Mode.PLAY, Mode.TEST_ENV]:
            printc("ERROR! The selected mode requires a run_id.", color="red")
        if cls.mode == Mode.TRAIN and cls.run_id is not None:
            raise ValueError("Nuh-uh! Mode is set to Mode.TRAIN, but run_id is not None."
                             " This will overwrite the existing model with specified run_id (if it exists)"
                             " - you most likely don't want that. If you do, manually delete the existing model.")


Config.verify_config()
