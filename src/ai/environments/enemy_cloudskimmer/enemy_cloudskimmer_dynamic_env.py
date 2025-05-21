from src.ai.environments.enemy_cloudskimmer.enemy_cloudskimmer_main_env import EnemyCloudSkimmerEnv


"""
Basically like main_env, except the player moves higher and lower, not just between pipes.
So agents learn how to fire at a moving target.

Why move higher and lower and not just between pipes?
So the agents keep learning how to hit trickshots, but also learn how to hit a moving target.
"""


class EnemyCloudSkimmerDynamicEnv(EnemyCloudSkimmerEnv):
    def __init__(self):
        super().__init__()

    def perform_step(self, action):
        # TODO: implement this
        pass

    def calculate_reward(self, action) -> int:
        # TODO: implement this
        pass
