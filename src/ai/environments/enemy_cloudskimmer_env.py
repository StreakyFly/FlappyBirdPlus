import numpy as np
import gymnasium as gym

import pygame

from .base_env import BaseEnv
from . import basic_flappy_state
from ..controllers.basic_flappy_controller import BasicFlappyModelController


class EnemyCloudskimmerEnv(BaseEnv):
    def __init__(self):
        super().__init__()
        self.basic_flappy_controller = BasicFlappyModelController()

    def get_action_and_observation_space(self):
        # index 0 -> 0: do nothing, 1: fire
        # index 1 -> 0: do nothing, 1: rotate up, 2: rotate down
        action_space = gym.spaces.MultiDiscrete([2, 3])

        # index 0 -> player y position
        # index 1 -> gun type (1 = Deagle, 2 = AK-47)

        # index 2 -> TODO gun rotation or enemy rotation? will the entire enemy rotate with the gun, or just gun?

        # TODO would it be better to always put first the main enemy, then the two behind, or should we put the first enemy as the one the agent is controlling, and then other two?
        #  I think always putting them in same order would be best. If enemy is dead, put placeholder position, something that never happens. Still ask Mr. ChatGPT what would be a good choice or if I should use a flag instead?
        # index 3 -> TODO just enemy y position? Or is x position necessary as well? It will be linked to gun type,
        # index 4 ->   TODO if gun type = 1, it will mean it's the front enemy, gun type = 2 will mean the enemy is
        # index 5 ->   TODO behind. So check if x position is always the same or does it slightly change? It shouldn't, but you never know...

        # TODO PIPE POSITIONS - maybe vertical center of all pipes? 4 pipes, so 4 y and 4 x positions
        # index 6 ->
        # index 7 ->
        # index 8 ->
        # index 9 ->
        # index 10 ->
        # index 11 ->
        # index 12 ->
        # index 13 ->

        # TODO bullet positions the agent fired? Ask Mr. ChatGPT if that's necessary or if DQN's big brain can figure
        #  out what's going on with the bullets based on the rewards the agent gets (if player is hit, or if they hit themselves)
        #  If having bullet positions would be easier, than include them - duh. When there's not enough bullets
        #  put placeholders or some values that would otherwise never happen or whatever would be good - flags maybe?
        # index 14 ->
        # index 15 ->
        # index 16 ->
        # index 17 ->

        observation_space = gym.spaces.Box(
            # low=np.array([-120, -15, -90, -265, 200, 125, 200, 515, 200, 905, 200], dtype=np.float32),
            # high=np.array([755, 19, 20, 300, 600, 510, 600, 900, 600, 1290, 600], dtype=np.float32),
            low=np.array([-120, ], dtype=np.float32),
            high=np.array([755, ], dtype=np.float32),
            dtype=np.float32
        )

        return action_space, observation_space

    def perform_step(self, action):
        # TODO train a single enemy cloudskimmer for each environment - all 3 cloudskimmers need to be present, but
        #  only one will be controlled by an agent, the other two will not be firing
        #  but make sure to change which one is the one firing during training, so it learns how to fire from all
        #  positions.

        # TODO take action
        # if action[0] == 1:
            # self.enemy_manager.spawned_enemy_groups[0].
        # cloudskimmer.fire;
        # if action[1] == 1:
        #   cloudskimmer.rotate_up
        # elif action[1] == 2:
        #   cloudskimmer.rotate_down

        terminated = False
        # TODO the only way for the agent to get terminated is for it to die from shooting itself

        for event in pygame.event.get():
            self.handle_quit(event)

        flappy_state = basic_flappy_state.get_state(self.player, self.pipes, self.get_pipe_pair_center)
        flappy_action = self.basic_flappy_controller.get_action(flappy_state)
        if flappy_action == 1:
            self.player.flap()

        self.background.tick()
        self.pipes.tick()
        self.floor.tick()
        self.player.tick()
        self.enemy_manager.tick()

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
        # TODO I think we can get all this info within the method, we don't have to pass it as an argument, do we?
        #  add boolean parameter something like shot_himself, if agent shoots itself, it should get punished
        #  add boolean parameter hit_pipe, so the agent gets a tiny reward if it hits a pipe

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
        #  - rotating? Maybe a lil tiny punishment if the agent rotates? So it won't rotate unnecessarily...?

        # small reward for not firing
        # if action[0] == 0:
        #     reward += 1
        # tiny reward for not rotating
        # if action[1] == 0:
        #     reward += 0.5

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
        print(self.enemy_manager.spawned_enemy_groups)
        # member = self.enemy_manager.spawned_enemy_groups[0].members[CURRENTLY_TRAINED_CLOUDSKIMMER]

        return reward
