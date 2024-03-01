import os
import asyncio
import cProfile

from src.flappybird import FlappyBird
from src.ai.flappy_bird_env import test_flappy_bird_env
from src.ai.train import train, run
from src.utils import printc


async def profile_flappy_bird():
    await FlappyBird().start()


MODES = ['play', 'train', 'train-headless', 'run-model']
MODE = 'train-headless'


if __name__ == "__main__":
    printc(f"Mode: {MODE}", color='green') if MODE in MODES else printc(f"Invalid mode: {MODE}", color='red')
    if MODE == 'play':
        asyncio.run(FlappyBird().start())
        # cProfile.run('asyncio.run(profile_flappy_bird())', sort='cumulative')
    elif MODE == 'train':
        train()
        # test_flappy_bird_env()
    elif MODE == 'train-headless':
        os.environ["SDL_VIDEODRIVER"] = "dummy"  # run pygame in headless mode to increase performance
        train()
    elif MODE == 'run-model':
        run()
