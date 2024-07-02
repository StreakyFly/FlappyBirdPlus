import numpy as np
import gymnasium as gym

import pygame

from .base_env import BaseEnv
from . import basic_flappy_state
# from ..controllers.basic_flappy_controller import BasicFlappyModelController
from ...entities.enemies import CloudSkimmer
from ...entities.items import Gun

"""
Randomly select one of the enemies to control.
Once that enemy dies, terminate the episode and select another one randomly.
"""


# TODO CHECK ALL TODO'S IN ALL SRC FILES BEFORE STARTING THE TRAINING,
#  CUZ THERE'S SOME QUESTIONABLE STUFF I LEFT FOR LATER


# TODO We should maybe end the episode if it lasts too long
# TODO ghosts need to be better shaded, more detail
# TODO (in cloudskimmer.py) ghost's eyes should follow the player (depending on gun rotation)
# TODO ghosts should spawn in random colors
#  as they get damaged, they should either change color orrr become more transparent
#  when they die, the weapon should fall to the ground and the ghost should disappear


class EnemyCloudskimmerEnv(BaseEnv):
    def __init__(self):
        super().__init__()
        # self.basic_flappy_controller = BasicFlappyModelController()
        self.controlled_enemy_id: int = -1  # 0: top, 1: middle, 2: bottom
        self.controlled_enemy: CloudSkimmer = None
        self.enemy_index_dict = {}  # map enemies to their initial index in the list

        self.pipes.spawn_initial_pipes_like_its_midgame()
        self.spawn_enemies()
        self.pick_random_enemy()

        self.temp_var_max_sizes = set()

    def reset_env(self):
        super().reset_env()
        self.pipes.spawn_initial_pipes_like_its_midgame()
        self.enemy_index_dict = {}
        self.spawn_enemies()
        self.pick_random_enemy()

    def spawn_enemies(self):
        self.enemy_manager.spawned_enemy_groups = []
        self.enemy_manager.spawn_cloudskimmer()
        # map enemies to their initial index in the list
        for i, enemy in enumerate(self.enemy_manager.spawned_enemy_groups[0].members):
            self.enemy_index_dict[enemy] = i

    def pick_random_enemy(self):
        self.controlled_enemy_id = 2 #np.random.randint(0, 3)  # TODO uncomment duh
        self.controlled_enemy = self.enemy_manager.spawned_enemy_groups[0].members[self.controlled_enemy_id]

    def get_action_and_observation_space(self):
        # index 0 -> 0: do nothing, 1: fire, 2: reload
        # index 1 -> 0: do nothing, 1: rotate up, 2: rotate down
        action_space = gym.spaces.MultiDiscrete([3, 3])

        # index 0 -> player y position
        # index 1 -> player y velocity
        # index 2 -> which enemy is being controlled (0: top, 1: middle, 2: bottom);
        #             gun type can be derived from this as guns are always in the same order
        # index 3 -> is the gun on cooldown (would providing exact cooldown time be better?)
        # index 4 -> remaining loaded bullets in the gun
        # index 5 -> gun rotation
        # index 6 -> x position of the controlled enemy
        # index 7 -> y position of the top enemy
        # index 8 -> y position of the middle enemy
        # index 9 -> y position of the bottom enemy
        # index 10 -> x position of vertical center of the first pipe (distance between pipes is always the same)
        # index 11 -> y position of vertical center of the first pipe
        # index 12 -> y position of vertical center of the second pipe
        # index 13 -> y position of vertical center of the third pipe
        # index 14 -> y position of vertical center of the fourth pipe
        # TODO x and y positions of N bullets. Bullet positions should be fixed. When the bullet despawns, put placeholder values that would never happen.
        #  For example if we have [pos1, pos2, empty_ph, pos4, empty_ph], and the agent fires another bullet, we put it in the first empty_ph slot we find.
        #  Figure out what to do if all slots are filled - replace the oldest bullet?
        #  If bullet hits the floor and stop is called, it should be excluded from the observation space
        # index 15 ->
        # index 16 ->
        # index 17 ->
        # index 18 ->
        # index 19 ->
        # index 20 ->

        observation_space = gym.spaces.Box(
            #                0    1  2  3   4    5     6    7    8    9    10   11   12   13   14
            low=np.array([-120, -17, 0, 0,  0, -60,  449, 457, 335, 207, -266, 272, 272, 272, 272, ], dtype=np.float32),
            high=np.array([755,  21, 2, 1, 30,  60, 1900, 493, 365, 243,  117, 528, 528, 528, 528, ], dtype=np.float32),
            dtype=np.float32
        )

        return action_space, observation_space

    def perform_step(self, action):
        for event in pygame.event.get():
            self.handle_quit(event)

        terminated = False
        if self.controlled_enemy not in self.enemy_manager.spawned_enemy_groups[0].members:
            terminated = True

        self.update_bullet_info()

        # self.handle_basic_flappy()

        self.background.tick()
        self.pipes.tick()
        self.floor.tick()
        self.player.tick()
        self.enemy_manager.tick()

        self.controlled_enemy.rotate_gun(action[1])

        self.controlled_enemy.shoot()
        # if action[0] == 0:
        #     pass  # do nothing
        # elif action[0] == 1:
        #     self.controlled_enemy.shoot()
        # elif action[0] == 2:
        #     self.controlled_enemy.reload()

        reward = self.calculate_reward(action=action)

        pygame.display.update()
        self.config.tick()

        return self.get_state(), reward, terminated, False

    def get_state(self):
        gun: Gun = self.controlled_enemy.gun
        is_gun_on_cooldown: bool = gun.interaction_in_progress
        gun_remaining_bullets = gun.quantity
        gun_rotation = gun.rotation

        controlled_enemy_x_pos = self.controlled_enemy.x

        # initialize an array of length 3 with placeholder values that can never happen
        enemy_y_positions = [0, 0, 0]
        if self.enemy_manager.spawned_enemy_groups:
            for enemy in self.enemy_manager.spawned_enemy_groups[0].members:
                # get the index the enemy had in the list when the episode started
                enemy_index = self.enemy_index_dict[enemy]
                # put the enemy's position in the array at that index
                enemy_y_positions[enemy_index] = enemy.y

        first_pipe_center_x_position = self.pipes.upper[0].x + self.pipes.upper[0].w // 2
        pipe_center_y_positions = []
        for i, pipe_pair in enumerate(zip(self.pipes.upper, self.pipes.lower)):
            pipe_center = self.get_pipe_pair_center(pipe_pair)
            pipe_center_y_positions.append(pipe_center[1])


        # TODO get positions of N bullets
        size = len(self.controlled_enemy.gun.shot_bullets)
        valid_count = 0
        for bullet in self.controlled_enemy.gun.shot_bullets:
            if bullet.stopped:
                continue
            valid_count += 1

        self.temp_var_max_sizes.add(valid_count)
        # print(self.temp_var_max_sizes, size, valid_count)


        game_state = np.array(
            [self.player.y,
             self.player.vel_y,
             self.controlled_enemy_id,
             is_gun_on_cooldown,
             gun_remaining_bullets,
             gun_rotation,
             controlled_enemy_x_pos] +
            enemy_y_positions +
            [first_pipe_center_x_position] +
            pipe_center_y_positions,
            # bullet_positions,  # TODO bullet positions
            dtype=np.float32)

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
        #     maybe even a slightly bigger punishment for each rotation direction change, so it won't look jittery

        # small reward for firing... or for not firing...?
        # if action[0] == 1:
        #     reward += 1
        # small reward for reloading
        # if action[0] == 2:
        #     reward += 10
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
        # member = self.enemy_manager.spawned_enemy_groups[0].members[CURRENTLY_TRAINED_CLOUDSKIMMER]

        return reward

    def handle_basic_flappy(self):
        flappy_state = basic_flappy_state.get_state(self.player, self.pipes, self.get_pipe_pair_center)
        flappy_action = self.basic_flappy_controller.get_action(flappy_state)
        if flappy_action == 1:
            self.player.flap()
