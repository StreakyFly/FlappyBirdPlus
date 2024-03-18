import src.ai.trainPPO as modelPPO
import src.ai.trainDQN as modelDQN
from modes import Mode
from src.ai.flappy_bird_env import FlappyBirdEnvManager, EnvType


config = {
    'model': modelDQN,  # <-- change the model here (modelDQN or modelPPO)
    'env_manager': FlappyBirdEnvManager(env_type=EnvType.BASIC_FLAPPY),  # <-- change environment type here
    'mode': Mode.RUN_MODEL,  # <-- change the mode here
    'options': {
        'headless': False,  # run pygame in headless mode to increase performance
        'profile': False,  # profile the code
    }
}
