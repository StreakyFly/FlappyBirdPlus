from .utils import printc

from .modes import Mode
from .ai.game_envs.env_types import EnvType


class Config:
    model = 'DQN'  # <-- change the model here (DQN or PPO)
    env_type = EnvType.BASIC_FLAPPY  # <-- change environment type here
    mode = Mode.RUN_MODEL  # <-- change the mode here

    options = {
        'headless': False,  # run pygame in headless mode to increase performance
        'mute': False,  # mute the audio (slight performance boost)
        'profile': False,  # profile the code
    }

    @classmethod
    def verify_config(cls):
        if cls.model not in ['DQN', 'PPO']:
            raise ValueError(f"Invalid model: {cls.model}")
        if cls.model != 'DQN':
            printc("WARNING! Only DQN model is fully supported at the moment.", color="yellow")
        if cls.options['headless'] and not cls.options['mute']:
            printc("WARNING! Headless mode is enabled but audio is not muted.", color="yellow")


Config.verify_config()
