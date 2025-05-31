import random
from typing import Literal

import numpy as np
import pygame

from src.ai.controllers import EnemyCloudSkimmerModelController
from src.ai.environments.enemy_cloudskimmer.enemy_cloudskimmer_main_env import EnemyCloudSkimmerEnv
from src.entities import PlayerMode, CloudSkimmer

# LMFAOOO great plan Mr. StreakyFly, great plan - worked like a charm! Once I deleted it and did something else.
"""
TODO: write this comment better, but like
A simpler environment compared to main_env.py, cuz pipes and player won't move, so agents
can first learn that they have to hit the target and how to hit trickshots
which should be much simpler to figure out when the target and the rest of the env isn't moving

The target should be static, but can move every 5 seconds or so, to different position, so
it doesn't overfit to one position. Same with the pipes.

TODO: maybe constantly move the player up and down? At different speeds? Cuz teleporting might be confusing.
"""


class EnemyCloudskimmerSimpleEnv(EnemyCloudSkimmerEnv):
    def __init__(self):
        super().__init__()
        # self.reset_env()  # TEMP: I don't think this is necessary, it's already called in base_env

        self.flap_state: Literal['flap_more', 'flap_less'] = 'flap_more'
        self.wait_until_next_flap = 3

    def reset_env(self):
        super().reset_env()
        self.player.set_mode(PlayerMode.TRAIN)
        self.player.reset_vals_normal()

        player_speed_factor = 0.3  # how fast the player moves
        self.player.vel_y = -16.875 * player_speed_factor  # player's velocity along Y axis
        self.player.max_vel_y = 19 * player_speed_factor  # 18.75  # max vel along Y, max descend speed
        self.player.min_vel_y = -15 * player_speed_factor  # min vel along Y, max ascend speed
        self.player.acc_y = 1.875 * player_speed_factor  # players downward acceleration
        self.player.vel_rot = -2.7 * player_speed_factor  # player's rotation speed
        self.player.flap_acc = -16.875 * player_speed_factor  # players speed on flapping

        self.player.set_tick_train(self.tick_player_up_and_down)
        # self.pipes.clear()
        # self.place_pipes_well()

    def pick_random_enemy(self):
        # self.controlled_enemy_id = np.random.randint(0, 3)
        # self.controlled_enemy_id = random.choice([0, 2]) # control either top or bottom enemy, but not the middle
        self.controlled_enemy_id = 2
        self.controlled_enemy = self.enemy_manager.spawned_enemy_groups[0].members[self.controlled_enemy_id]

        for enemy in self.enemy_manager.spawned_enemy_groups[0].members:  # type: CloudSkimmer
            if enemy.id != self.controlled_enemy_id:
                enemy.set_max_hp(50)  # make other enemies weaker
                continue
            enemy.set_max_hp(100_000)  # don't let the controlled enemy die
            enemy.gun.shoot_cooldown = 5  # make it shoot faster for training to make rewards less sparse
            enemy.gun.reload_cooldown = 5  # "remove" reload cooldown
            # enemy.gun.ammo_speed = 52  # speed of deagle bullets  # I think learning with default bullet speed is
            #  better, because I think it would be difficult to adapt to lower speed later on

    def perform_step(self, action):
        self.step += 1
        for event in pygame.event.get():
            self.handle_quit(event)

        # spawn new randomly positioned pipes every 360 ticks
        # if self.step % 360 == 0:
        #     self.pipes.spawn_initial_pipes_like_its_midgame()
        #     self.place_pipes_well()

        EnemyCloudSkimmerModelController.perform_action(self.controlled_enemy, action)

        self.background.draw()
        self.pipes.tick()
        self.floor.draw()
        self.player.tick()
        self.enemy_manager.tick()

        pygame.display.update()
        self.config.tick()

        return (
            self.get_observation(),  # observation
            self.calculate_reward(action=action),  # reward,
            self.controlled_enemy not in self.enemy_manager.spawned_enemy_groups[0].members,  # terminated
            self.step > 1200,  # truncated - end the episode if it lasts too long
            {}  # info
        )

    def get_observation(self) -> dict[str, np.ndarray]:
        obs = super().get_observation()

        # TEMP: set weapon type to a random value, so agent doesn't start ignoring the
        #  value as it wouldn't change otherwise
        obs['controlled_enemy_extra_info'][0] = random.choice([0, 1])

        return obs

    def get_action_masks(self) -> np.ndarray:
        action_masks = super().get_action_masks()

        # don't let the agent reload (yet)
        action_masks[0][2] = 0

        return action_masks

    def calculate_reward(self, action) -> int:
        """
        Focus on hitting the target, with a trickshot if necessary.
        """
        reward = 0

        # lil punishment when firing
        if action[0] == 1:
            reward -= 0.2  # TEMP: 0.3 was pretty good, but maybe too much, scared top enemy from firing

        for bullet in self.all_bullets_from_last_frame.union(self.controlled_enemy.gun.shot_bullets):
            # reward for hitting the player
            if bullet.hit_entity == 'player':
                reward += 5
                # bonus reward if the bullet hit the player after bouncing
                if bullet.bounced:
                    reward += 3
            # punishment for hitting himself or his teammates
            elif bullet.hit_entity == 'enemy':
                reward -= 1
            # punishment for hitting the ground
            elif bullet.hit_entity == 'floor':
                reward -= 0.2
            # reward for hitting a pipe
            elif bullet.hit_entity == 'pipe' and bullet not in self.bullets_bounced_off_pipes:
                self.bullets_bounced_off_pipes.add(bullet)
                reward += 0.05

            # punishment if bullet disappears without hitting the player
            # elif bullet not in self.controlled_enemy.gun.shot_bullets and bullet.hit_entity != 'player':
            #     reward -= 0.2

        self.all_bullets_from_last_frame = set(self.controlled_enemy.gun.shot_bullets)

        return reward

    def tick_player_up_and_down(self) -> None:
        # keep in mind 0 is on top, so top bound is LOWER than bottom bound
        top_bound, bottom_bound = self.get_valid_player_bounds()

        self.wait_until_next_flap -= 1

        if self.wait_until_next_flap <= 0:
            self.player.flap()

        if self.flap_state == 'flap_more':
            if self.player.y > top_bound:
                if self.wait_until_next_flap <= 0:
                    self.wait_until_next_flap = random.randint(6, 16)
            else:
                self.flap_state = 'flap_less'
        elif self.flap_state == 'flap_less':
            if self.player.y < bottom_bound:
                if self.wait_until_next_flap <= 0:
                    self.wait_until_next_flap = random.randint(22, 34)
            else:
                self.player.flap()
                self.flap_state = 'flap_more'
        self.player.tick_normal()

    def get_valid_player_bounds(self, max_offset: int = 210) -> tuple[float, float]:
        """
        Returns the valid bounds for the player's Y position.
        The player should not be able to go too high or too low.
        """
        next_pipe_pair = None
        for upper_pipe, lower_pipe in zip(self.pipes.upper, self.pipes.lower):
            if upper_pipe.x + upper_pipe.w > self.player.x:
                next_pipe_pair = (upper_pipe, lower_pipe)
                break

        next_pipe_pair_center_y = self.get_pipe_pair_center(next_pipe_pair)[1]

        top_bound = pygame.math.clamp(
            (next_pipe_pair_center_y - self.player.h // 2) - max_offset,
            self.player.min_y,
            self.player.max_y
        )
        bottom_bound = pygame.math.clamp(
            (next_pipe_pair_center_y + self.player.h // 2) + max_offset,
            self.player.min_y,
            self.player.max_y
        )

        # keep in mind 0 is on top, so top bound is LOWER than bottom bound
        return top_bound, bottom_bound

    # def move_player_to_new_position(self):
    #     """
    #     Moves the player to a random position.
    #     """
    #     next_pipe_pair = None
    #     for upper_pipe, lower_pipe in zip(self.pipes.upper, self.pipes.lower):
    #         if upper_pipe.x + upper_pipe.w > self.player.x:
    #             next_pipe_pair = (upper_pipe, lower_pipe)
    #             break
    #
    #     next_pipe_pair_center_y = self.get_pipe_pair_center(next_pipe_pair)[1]
    #
    #     random_offset = random.randint(-300, 300)  # how far from the next pipe center can the player be (on y-axis)
    #     self.player.y = np.clip(
    #         a=(next_pipe_pair_center_y - self.player.h // 2) + random_offset,
    #         a_min=self.player.min_y,
    #         a_max=self.player.max_y
    #     )
    #     self.player.rotation = random.randint(-90, 20)

    def place_pipes_well(self) -> None:
        """
        Places the pipes in a way that they don't overlap with the player's X position.
        """
        def are_pipes_well_placed() -> bool:
            for pipe in self.pipes.upper + self.pipes.lower:
                if self.player.x + self.player.w > pipe.x and self.player.x < pipe.x + pipe.w:
                    return False
            return True

        while not are_pipes_well_placed():
            self.pipes.spawn_initial_pipes_like_its_midgame()
        # self.move_player_to_new_position()
