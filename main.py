import asyncio
import cProfile

from src.flappybird import FlappyBird


async def profile_flappy_bird():
    await FlappyBird().start()

if __name__ == "__main__":
    asyncio.run(FlappyBird().start())
    # cProfile.run('asyncio.run(profile_flappy_bird())', sort='cumulative')
