import sys
import numpy as np

import pygame
from pygame import QUIT

from .base_env import BaseEnv


class EnemyCloudskimmerEnv(BaseEnv):
    def __init__(self):
        super().__init__()

    def get_action_and_observation_space(self):
        # # self.action_space = gym.spaces.MultiDiscrete([2, 3])  # for multiple actions
        # action_space = gym.spaces.Discrete(2)  # 0: do nothing, 1: flap the wings
        # observation_space = gym.spaces.Box(
        #     # low=np.array([-120, -15, -90, -265, 200, 125, 200, 515, 200, 905, 200], dtype=np.float32),
        #     # high=np.array([755, 19, 20, 300, 600, 510, 600, 900, 600, 1290, 600], dtype=np.float32),
        #     low=np.array([-120, -17, 0, -650, -650], dtype=np.float32),
        #     high=np.array([755, 21, 500, 550, 550], dtype=np.float32),
        #     dtype=np.float32
        # )
        return NotImplementedError("get_action_and_observation_space() method has not been implemented yet")

        action_space = None
        observation_space = None

        return action_space, observation_space

    def perform_step(self, action):
        # TODO train a single enemy cloudskimmer for each environment - all 3 cloudskimmers needs to be present, but
        #  only one will be controlled by an agent, the other two will not be firing
        #  but make sure to change which one is the one firing during training, so it learns how to fire from all
        #  positions.

        # TODO take action - did I miss any action?
        # if action[0] == 1:
        #   cloudskimmer.fire
        # if action[1] == 1:
        #   cloudskimmer.rotate_up
        # elif action[1] == 2:
        #   cloudskimmer.rotate_down

        terminated = False

        # TODO probs also remove this, because player hitting the pipe has "nothing" to do with the enemy agent
        # self.player.handle_bad_collisions(self.pipes, self.floor)
        # if self.is_player_dead():
        #     terminated = True

        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                sys.exit()

        self.background.tick()
        self.pipes.tick()
        self.floor.tick()
        self.player.tick()
        self.score.tick()

        reward = self.calculate_reward(action=action)

        pygame.display.update()
        self.config.tick()

        return self.get_state(), reward, terminated, False

    def get_state(self):
        # TODO modify the state, as we are missing:
        #   - current enemy position
        #   - current enemy rotation
        #   - current enemy teammates' positions
        #   - gun type
        #   - maybe even bullet locations? or maybe not...? It could learn how bullets interact just by seeing when the
        #     player gets damaged or not? although if they fire multiple bullets it will be hard to tell which bullet
        #     caused the damage

        pipe_center_positions = []
        for i, pipe_pair in enumerate(zip(self.pipes.upper, self.pipes.lower)):
            pipe_center = self.get_pipe_pair_center(pipe_pair)
            pipe_center_positions.extend(pipe_center)

        game_state = np.array([self.player.y, self.player.vel_y] + pipe_center_positions, dtype=np.float32)
        return game_state

    def calculate_reward(self, action) -> int:
        reward = 0

        # TODO implement this method
        #  Agent should be rewarded for:
        #  - hitting/damaging the player (big reward)
        #  - hitting a pipe (small reward) - so the likelihood of learning a cool bounce-off-pipe strategy is higher
        #  - not firing (small reward each frame the agent doesn't fire, so if he fires but doesn't hit the player, he
        #    won't get the reward, which is like if he got punished - punishing him if bullet despawns without hitting
        #    the player might be more logical, however not only is it harder to implement, it might also confuse the
        #    agent that he was punished after one bullet's position changed to a placeholder - or if he won't know
        #    bullet positions, he would be confused why he was randomly punished a few frames after firing
        #  Agent should be punished for:
        #  - hitting himself or his teammates (big punishment)

        print("WARNING! 'calculate_reward_enemy_cloudskimmer' is not yet implemented!")

        # small reward for not firing
        # if action[0] == 0:
        #     reward += 1

        # for bullet in enemy.weapon:
        #   small reward for hitting a pipe
        #   if bullet.self.hit_entity == 'pipe':
        #       reward += 2
        #   big reward for hitting the player
        #   if bullet.self.hit_entity == 'player':
        #       reward += 300
        #   big punishment for hitting himself or his teammates
        #   if bullet.self.hit_entity == 'enemy':
        #       reward -= 100

        # get gun object
        CURRENTLY_TRAINED_CLOUDSKIMMER = 1  # 0, 1 or 2
        member = self.enemy_manager.spawned_enemy_groups[0].members[CURRENTLY_TRAINED_CLOUDSKIMMER]

        return reward
