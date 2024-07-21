import numpy as np
import weakref
import gymnasium as gym

import pygame

from .base_env import BaseEnv
from . import basic_flappy_state
from ..controllers.basic_flappy_controller import BasicFlappyModelController
from ...entities.enemies import CloudSkimmer
from ...entities.items import Gun

"""
Randomly select one of the enemies to control.
Once that enemy dies, terminate the episode and select another one randomly.
"""


# TODO CHECK ALL TODO'S IN ALL SRC FILES BEFORE STARTING THE TRAINING,
#  CUZ THERE'S SOME QUESTIONABLE STUFF I LEFT FOR LATER

# TODO Should the player fly more randomly for a part of training, not just between pipes? So the agents hopefully learn
#  some epic bounce tricks to hit the player, instead of just aiming at the player's current position.

"""
Masking Bullet Data:
During the later stages of training, static placeholder values for bullet info should be introduced.
This step teaches the model to gradually ignore these inputs, which are not critical for decision-making post-training.
It ensures that during deployment, the model can operate effectively even when bullet data is not provided.
"""


class EnemyCloudskimmerEnv(BaseEnv):
    requires_action_masking = True

    def __init__(self):
        super().__init__()
        self.step: int = 0  # step counter
        self.basic_flappy_controller = BasicFlappyModelController()
        self.controlled_enemy_id: int = -1  # 0: top, 1: middle, 2: bottom
        self.controlled_enemy: CloudSkimmer = None
        self.enemy_index_dict = {}  # map enemies to their initial index in the list
        self.bullet_index_dict = weakref.WeakKeyDictionary()  # map bullets to their initial index in the list
        self.replaced_bullets = weakref.WeakSet()  # old bullets that were replaced by new ones in the observation space

        self.pipes.spawn_initial_pipes_like_its_midgame()
        self.spawn_enemies()
        self.pick_random_enemy()

        # --- stuff needed to calculate the reward ---
        # When the bullet hits the player or an enemy, it gets immediately removed from the gun.shot_bullets set, so we
        # can't see if it hit the player or an enemy, that's why we store references to all bullets from the last frame.
        self.all_bullets_from_last_frame = set()
        self.bullets_bounced_off_pipes = weakref.WeakSet()

    def reset_env(self):
        super().reset_env()
        self.step = 0
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
        self.controlled_enemy_id = np.random.randint(0, 3)
        self.controlled_enemy = self.enemy_manager.spawned_enemy_groups[0].members[self.controlled_enemy_id]

    # @staticmethod
    # def get_action_and_observation_space() -> tuple[gym.spaces.MultiDiscrete, gym.spaces.Box]:
    #     # index 0 -> 0: do nothing, 1: fire, 2: reload
    #     # index 1 -> 0: do nothing, 1: rotate up, 2: rotate down
    #     action_space = gym.spaces.MultiDiscrete([3, 3])
    #
    #     # TODO if you decide to change CloudSkimmer's movement so they aren't "linked"
    #     #  add X positions of all cloud skimmers, not just the controlled one!
    #
    #     # TODO removed gun shoot cooldown and reload cooldown from observation space,
    #     #  as they're now handled by the action masks
    #
    #     # index 0 -> player y position
    #     # index 1 -> player y velocity
    #     # index 2 -> which enemy is being controlled (0: top, 1: middle, 2: bottom);
    #     #             gun type can be derived from this as guns are always in the same order
    #     # index 3 -> remaining loaded bullets in the gun
    #     # index 4 -> gun rotation
    #     # index 5 -> x position of the controlled enemy
    #     # index 6 -> flag - does the top enemy exist (0: no, 1: yes)
    #     # index 7 -> y position of the top enemy
    #     # index 8 -> flag - does the middle enemy exist (0: no, 1: yes)
    #     # index 9 -> y position of the middle enemy
    #     # index 10 -> flag - does the bottom enemy exist (0: no, 1: yes)
    #     # index 11 -> y position of the bottom enemy
    #     # index 12 -> x position of vertical center of the first pipe (distance between pipes is always the same)
    #     # index 13 -> y position of vertical center of the first pipe
    #     # index 14 -> y position of vertical center of the second pipe
    #     # index 15 -> y position of vertical center of the third pipe
    #     # index 16 -> y position of vertical center of the fourth pipe
    #     #
    #     # Up - bullet gets removed off-screen => 0 + max height of bullet = -24 ~ -20 (can't be fired at 90 angle)
    #     # Down - bullet gets stopped when hitting floor => 797
    #     # Left - bullet before -256 is useless as it can't bounce back => -256
    #     # Right - bullet after 1144 is useless as it can't bounce back => 1144 (1144, because that's the first point
    #     #  where CloudSkimmers can fire from, if the x is larger, that means the bullet bounced and flew past them)
    #     # index 17 -> flag - does b1 exist (0: no, 1: yes)
    #     # index 18 -> b1.front_pos.x
    #     # index 19 -> b1.front_pos.y
    #     # index 20 -> flag - does b2 exist (0: no, 1: yes)
    #     # index 21 -> b2.front_pos.x
    #     # index 22 -> b2.front_pos.y
    #     # index 23 -> ...
    #
    #     # The problem with using spaces.Box is that not only is it less readable, but it also doesn't allow us to
    #     # choose which values get normalized and which don't. For example, we don't want to normalize the flags.
    #     observation_space = gym.spaces.Box(
    #         #                0    1  2  3    4    5   6    7  8    9  10  11    12      13 - 16    17   18   19 - 46
    #         low=np.array([-120, -17, 0, 0, -60, 449,  0, 207, 0, 335, 0, 457, -265] + [272] * 4 + [0, -256, -20] * 10, dtype=np.float32),
    #         high=np.array([755,  21, 2, 30, 60, 1900, 1, 243, 1, 365, 1, 493,  118] + [528] * 4 + [1, 1144, 797] * 10, dtype=np.float32),
    #         dtype=np.float32
    #     )
    #
    #     return action_space, observation_space

    @staticmethod
    def get_action_and_observation_space() -> tuple[gym.spaces.MultiDiscrete, gym.spaces.Dict]:
        # index 0 -> 0: do nothing, 1: fire, 2: reload
        # index 1 -> 0: do nothing, 1: rotate up, 2: rotate down
        action_space = gym.spaces.MultiDiscrete([3, 3])

        observation_space = gym.spaces.Dict({
            'player_y_position': gym.spaces.Box(low=-120, high=755, shape=(1,), dtype=np.float32),
            'player_y_velocity': gym.spaces.Box(low=-17, high=21, shape=(1,), dtype=np.float32),
            'controlled_enemy': gym.spaces.Discrete(3),
            'remaining_bullets': gym.spaces.Box(low=0, high=30, shape=(1,), dtype=np.float32),
            'gun_rotation': gym.spaces.Box(low=-60, high=60, shape=(1,), dtype=np.float32),
            'enemy_x_position': gym.spaces.Box(low=449, high=1900, shape=(1,), dtype=np.float32),
            'enemy_existence': gym.spaces.MultiBinary(3),
            'top_enemy_y_position': gym.spaces.Box(low=207, high=243, shape=(1,), dtype=np.float32),
            'middle_enemy_y_position': gym.spaces.Box(low=335, high=365, shape=(1,), dtype=np.float32),
            'bottom_enemy_y_position': gym.spaces.Box(low=457, high=493, shape=(1,), dtype=np.float32),
            'first_pipe_x_position': gym.spaces.Box(low=-265, high=118, shape=(1,), dtype=np.float32),
            'pipe_y_positions': gym.spaces.Box(low=272, high=528, shape=(4,), dtype=np.float32),
            'bullet_existence': gym.spaces.MultiBinary(10),
            'bullet_positions': gym.spaces.Box(low=np.array([-256, -20]*10, dtype=np.float32), high=np.array([1144, 797]*10, dtype=np.float32), dtype=np.float32)
        })

        return action_space, observation_space

    @staticmethod
    def get_observation_space_clip_modes() -> dict[str, int]:
        observation_space_clip_modes = {
            'player_y_position': 1,
            'player_y_velocity': 1,
            'controlled_enemy': -1,
            'remaining_bullets': -1,
            'gun_rotation': -1,
            'enemy_x_position': 1,
            'enemy_existence': -1,
            'top_enemy_y_position': 1,
            'middle_enemy_y_position': 1,
            'bottom_enemy_y_position': 1,
            'first_pipe_x_position': 1,
            'pipe_y_positions': 1,
            'bullet_existence': -1,
            'bullet_positions': 1
        }
        return observation_space_clip_modes

    def perform_step(self, action):
        # print("PERFORMING STEP")
        self.step += 1
        for event in pygame.event.get():
            self.handle_quit(event)

        self.handle_basic_flappy()

        self.controlled_enemy.rotate_gun(action[1])

        if action[0] == 0:
            pass
        elif action[0] == 1:
            self.controlled_enemy.shoot()
        elif action[0] == 2:
            self.controlled_enemy.reload()

        self.update_bullet_info()

        self.background.tick()
        self.pipes.tick()
        self.floor.tick()
        self.player.tick()
        self.enemy_manager.tick()

        pygame.display.update()
        self.config.tick()

        # state = self.get_state()
        # reward = self.calculate_reward(action=action)
        # print("STEP DONE")
        # print()  # breakpoint here

        # return (state,
        return (self.get_state(),  # observation
                # reward,
                self.calculate_reward(action=action),  # reward,
                self.controlled_enemy not in self.enemy_manager.spawned_enemy_groups[0].members,  # terminated
                self.step > 1200,  # truncated; end the episode if it lasts too long
                {})  # info

    def get_state(self):
        first_pipe_center_x_position = self.pipes.upper[0].x + self.pipes.upper[0].w // 2
        pipe_center_y_positions = []
        for i, pipe_pair in enumerate(zip(self.pipes.upper, self.pipes.lower)):
            pipe_center = self.get_pipe_pair_center(pipe_pair)
            pipe_center_y_positions.append(pipe_center[1])

        gun: Gun = self.controlled_enemy.gun

        # game_state = np.array(
        #     [self.player.y,
        #      self.player.vel_y,
        #      self.controlled_enemy_id,
        #      # int(bool(gun.remaining_shoot_cooldown)),  # is the gun on shoot cooldown (1) or not (0)
        #      # int(bool(gun.remaining_reload_cooldown)),  # is the gun on reload cooldown (1) or not (0)
        #      gun.quantity,  # remaining loaded bullets in the gun
        #      gun.rotation,
        #      self.controlled_enemy.x] +
        #     self.get_enemy_info_old() +
        #     [first_pipe_center_x_position] +
        #     pipe_center_y_positions +
        #     self.get_bullet_info_old(gun),
        #     dtype=np.float32)

        enemy_existence, enemy_y_pos = self.get_enemy_info()
        bullet_existence, bullet_pos = self.get_bullet_info(gun)

        game_state = {
            'player_y_position': np.array([self.player.y], dtype=np.float32),
            'player_y_velocity': np.array([self.player.vel_y], dtype=np.float32),
            'controlled_enemy': self.controlled_enemy_id,
            'remaining_bullets': np.array([gun.quantity], dtype=np.float32),
            # this is gun's raw rotation - animation_rotation is not taken into account
            'gun_rotation': np.array([self.controlled_enemy.gun_rotation], dtype=np.float32),
            'enemy_x_position': np.array([self.controlled_enemy.x], dtype=np.float32),
            'enemy_existence': np.array(enemy_existence, dtype=np.float32),
            'top_enemy_y_position': np.array([enemy_y_pos[0]], dtype=np.float32),
            'middle_enemy_y_position': np.array([enemy_y_pos[1]], dtype=np.float32),
            'bottom_enemy_y_position': np.array([enemy_y_pos[2]], dtype=np.float32),
            'first_pipe_x_position': np.array([first_pipe_center_x_position], dtype=np.float32),
            'pipe_y_positions': np.array(pipe_center_y_positions, dtype=np.float32),
            'bullet_existence': np.array(bullet_existence, dtype=np.float32),
            'bullet_positions': np.array(bullet_pos, dtype=np.float32)
        }

        return game_state

    def get_action_masks(self) -> np.ndarray:
        # initialize masks for each action type, all actions are initially available
        fire_reload_masks = np.ones(3, dtype=int)  # [do nothing, fire, reload]
        rotation_masks = np.ones(3, dtype=int)  # [do nothing, rotate up, rotate down]

        gun: Gun = self.controlled_enemy.gun

        # gun can't be neither fired nor reloaded if it's on reload cooldown
        if gun.remaining_reload_cooldown > 0:
            fire_reload_masks[1] = 0  # disable fire
            fire_reload_masks[2] = 0  # disable reload

        # gun can't be fired if it's on shoot cooldown or if there's no ammo left in the gun
        if gun.remaining_shoot_cooldown > 0 or gun.quantity <= 0:
            fire_reload_masks[1] = 0  # disable fire

        # gun "can't" be reloaded if it's already full or if there's no ammo left in the inventory
        if gun.quantity == gun.magazine_size or gun.ammo_item.quantity <= 0:
            fire_reload_masks[2] = 0  # disable reload

        action_masks = np.array([fire_reload_masks, rotation_masks])
        return action_masks

    def calculate_reward(self, action) -> int:
        """
        Agent should be rewarded for:
         - hitting/damaging the player (huge reward) + bonus, if the bullet hit the player after bouncing off a pipe
         - hitting a pipe (small reward) - so the likelihood of learning a cool bounce-off-pipe strategy is higher
         - not firing (small reward each frame the agent doesn't fire, so if he fires but doesn't hit the player, he
           won't get the reward, which is like if he got punished - punishing him if bullet despawns without hitting
           the player might be more logical, however not only is it harder to implement, it might also confuse the
           agent that he was punished after one bullet's position changed to a placeholder)
        Agent should be punished for:
         - hitting himself or his teammates (big punishment)
         - rotating? Maybe a lil tiny punishment if the agent rotates? So it won't rotate unnecessarily...?
           maybe even a slightly bigger punishment for each rotation direction change, so it won't look jittery
        """
        reward = 0

        # small punishment for firing
        if action[0] == 1:
            reward -= 1
        # medium reward for reloading
        elif action[0] == 2:
            reward += 10

        # tiny reward for not rotating
        if action[1] == 0:
            reward += 0.3
        # small punishment for rotation direction change
        # if prev_rotation_action != action[1]:
        #     reward -= 2

        for bullet in self.all_bullets_from_last_frame.union(self.controlled_enemy.gun.shot_bullets):
            # huge reward for hitting the player
            if bullet.hit_entity == 'player':
                reward += 300
                # bonus reward if the bullet hit the player after bouncing
                # if bullet.bounced:
                #     reward += 300
            # big punishment for hitting himself or his teammates
            elif bullet.hit_entity == 'enemy':
                reward -= 100
            # small reward for hitting a pipe
            elif bullet.hit_entity == 'pipe' and bullet not in self.bullets_bounced_off_pipes:
                self.bullets_bounced_off_pipes.add(bullet)
                reward += 2

        self.all_bullets_from_last_frame = set(self.controlled_enemy.gun.shot_bullets)

        if abs(reward) > 11:
            print(reward, end=', ')

        return reward

    def handle_basic_flappy(self):
        flappy_state = basic_flappy_state.get_state(self.player, self.pipes, self.get_pipe_pair_center)
        flappy_action = self.basic_flappy_controller.predict_action(flappy_state)
        if flappy_action == 1:
            self.player.flap()

    def get_enemy_info_old(self):
        enemy_info = [0, 0] * 3  # 3 enemies max, flag whether that enemy exists, and its y position
        if self.enemy_manager.spawned_enemy_groups:
            for enemy in self.enemy_manager.spawned_enemy_groups[0].members:
                # get the index the enemy had in the list when the episode started
                enemy_index = self.enemy_index_dict[enemy]
                enemy_info[enemy_index    ] = 1
                enemy_info[enemy_index + 1] = enemy.y

        return enemy_info

    def get_enemy_info(self):
        # 3 enemies max
        enemy_existence = [0] * 3  # flag whether that enemy exists or not
        enemy_y_pos = [0] * 3  # enemy's y position
        if self.enemy_manager.spawned_enemy_groups:
            for enemy in self.enemy_manager.spawned_enemy_groups[0].members:
                # get the index the enemy had in the list when the episode started
                enemy_index = self.enemy_index_dict[enemy]
                enemy_existence[enemy_index] = 1
                enemy_y_pos[enemy_index] = enemy.y

        return enemy_existence, enemy_y_pos

    def get_bullet_info(self, gun):
        """
        Get information about bullets fired by the gun.
        The information is stored in two lists, bullet_exists and bullet_positions.
        The list bullet_existence contains flags whether the bullet exists or not.
        The list bullet_positions contains x and y positions (curr_front_pos) of the bullets.
        Bullets should always be put in the same slot in the lists as long as the bullet exist.
        If we have [pos1, pos2, empty_ph, pos4, empty_ph], and the agent fires another bullet,
        we put it in the first empty_ph slot we find. If all slots are filled we replace the oldest bullet.
        If bullet isn't useful, it shouldn't be included. For example if it hit the floor and got stopped.

        :param gun: Gun object that fired the bullets
        :return: List of bullet info (0: does the bullet exist, 1: bullet x position, 2: bullet y position) * 10 bullets
        """

        new_bullet = None
        # 10 bullets max
        bullet_existence = [0] * 10  # flag whether that bullet exists or not
        bullet_pos = [0, 0] * 10  # bullet's x and y position (curr_front_pos)

        # update the array with bullet positions of previously fired bullets (if they still exist)
        for bullet in gun.shot_bullets:
            if not self.is_bullet_info_useful(bullet):
                continue

            if bullet not in self.bullet_index_dict:
                if bullet.frame == 0:  # if bullet.frame > 0, it means that bullet's slot was taken by a newer bullet
                    new_bullet = bullet
                continue

            bullet_index = self.bullet_index_dict[bullet]
            bullet_existence[bullet_index] = 1
            bullet_pos[bullet_index * 2] = bullet.curr_front_pos.x  # bullet.x
            bullet_pos[bullet_index * 2 + 1] = bullet.curr_front_pos.y  # bullet.y

        # if a new bullet was fired, put it in the first free slot or replace the oldest bullet if all slots are filled
        if new_bullet:
            try:  # replace the first free slot
                replace_bullet_index = bullet_existence.index(0)
            # (this exception will be thrown very rarely, if ever, as it's very unlikely that all slots are filled)
            except ValueError:  # replace the oldest bullet
                oldest_bullet = None
                oldest_bullet_age = 0
                for bullet in gun.shot_bullets:
                    if not self.is_bullet_info_useful(bullet):
                        continue

                    if bullet.frame > oldest_bullet_age and bullet not in self.replaced_bullets:
                        oldest_bullet_age = bullet.frame
                        oldest_bullet = bullet

                self.replaced_bullets.add(oldest_bullet)
                replace_bullet_index = self.bullet_index_dict[oldest_bullet]
                del self.bullet_index_dict[oldest_bullet]

            self.bullet_index_dict[new_bullet] = replace_bullet_index
            bullet_existence[replace_bullet_index] = 1
            bullet_pos[replace_bullet_index * 2] = new_bullet.curr_front_pos.x  # new_bullet.x
            bullet_pos[replace_bullet_index * 2 + 1] = new_bullet.curr_front_pos.y  # new_bullet.y

        return bullet_existence, bullet_pos

    def get_bullet_info_old(self, gun):
        """
        Get information about bullets fired by the gun.
        The information is stored in a list of size 30, where each bullet takes up 3 slots.
        First slot is a flag whether that bullet exists or not, second and third are x and y position (curr_bullet_pos)
        of the bullet. Bullets should always be put in the same slot in bullet_info as long as they exist.
        If we have [pos1, pos2, empty_ph, pos4, empty_ph], and the agent fires another bullet,
        we put it in the first empty_ph slot we find. If all slots are filled we replace the oldest bullet.
        If bullet isn't useful, it shouldn't be included. For example if it hit the floor and got stopped.

        :param gun: Gun object that fired the bullets
        :return: List of bullet info (0: does the bullet exist, 1: bullet x position, 2: bullet y position) * 10 bullets
        """

        new_bullet = None
        bullet_info = [0, 0, 0] * 10  # 10 bullets max, flag whether that bullet exists, and its x and y position

        # update the array with bullet positions of previously fired bullets (if they still exist)
        for bullet in gun.shot_bullets:
            if not self.is_bullet_info_useful(bullet):
                continue

            if bullet not in self.bullet_index_dict:
                if bullet.frame == 0:  # if bullet.frame > 0, it means that bullet's slot was taken by a newer bullet
                    new_bullet = bullet
                continue

            bullet_index = self.bullet_index_dict[bullet]
            bullet_info[bullet_index    ] = 1
            bullet_info[bullet_index + 1] = bullet.curr_front_pos.x  # bullet.x
            bullet_info[bullet_index + 2] = bullet.curr_front_pos.y  # bullet.y

        # if a new bullet was fired, put it in the first free slot or replace the oldest bullet if all slots are filled
        if new_bullet:
            try:  # replace the first free slot
                replace_bullet_index = bullet_info.index(0)
            # (this exception will be thrown very rarely, if ever, as it's very unlikely that all slots are filled)
            except ValueError:  # replace the oldest bullet
                oldest_bullet = None
                oldest_bullet_age = 0
                for bullet in gun.shot_bullets:
                    if not self.is_bullet_info_useful(bullet):
                        continue

                    if bullet.frame > oldest_bullet_age and bullet not in self.replaced_bullets:
                        oldest_bullet_age = bullet.frame
                        oldest_bullet = bullet

                self.replaced_bullets.add(oldest_bullet)
                replace_bullet_index = self.bullet_index_dict[oldest_bullet]
                del self.bullet_index_dict[oldest_bullet]

                print("################\nage:", oldest_bullet_age, "index:", replace_bullet_index)

            self.bullet_index_dict[new_bullet] = replace_bullet_index
            bullet_info[replace_bullet_index    ] = 1
            bullet_info[replace_bullet_index + 1] = new_bullet.curr_front_pos.x  # new_bullet.x
            bullet_info[replace_bullet_index + 2] = new_bullet.curr_front_pos.y  # new_bullet.y

        print(bullet_info)
        return bullet_info

    def is_bullet_info_useful(self, bullet):
        """
        Check if the bullet is useful for the observation space.

        Up: bullet is deleted after flying off-screen on top, no need to handle it here
        Down: bullet hit the floor and got stopped
        Right: bullet was flying to the left, bounced back and flew past all the CloudSkimmers to the right
        Left: bullet was flying to the left, bounced off the top/bottom side of pipe and flew past the player to the left
        """
        # down - bullet hit the floor
        if bullet.stopped:
            return False

        # right - bullet flew past CloudSkimmers and can't return
        if bullet.bounced and bullet.x > (max(bullet.enemies, key=lambda enemy: enemy.x).x + bullet.enemies[0].w):
            return False

        # left - bullet flew past the player and can't return
        if bullet.bounced and bullet.velocity.x < 0 and (bullet.x + bullet.w) < self.player.x:
            return False

        return True
