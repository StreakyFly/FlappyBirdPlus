import random
from typing import Literal

import numpy as np
import pygame
from torch import nn

from src.ai.controllers import EnemyCloudSkimmerModelController
from src.ai.normalizers.vec_box_only_normalize import VecBoxOnlyNormalize
from src.ai.training_config import TrainingConfig
from src.entities import PlayerMode, CloudSkimmer
from .enemy_cloudskimmer_main_env import EnemyCloudSkimmerEnv


class EnemyCloudSkimmerStep1Env(EnemyCloudSkimmerEnv):
    """
    This simplified environment is the first step in training the enemy CloudSkimmer agent.
    The agent should learn to hit the target either directly, or with a trickshot if necessary,
    and shouldn't worry a lot about hitting its teammates or self, or when to reload.

    Key features:
    - Only the top and bottom enemies are controlled by the agent; the middle one is excluded.
    - Reloading is masked, so the agent doesn't have to worry about it just yet.
    - The player movement is drastically slowed down, so its randomness isn't that big of a problem.

    Observations:
    I noticed that agent trained with player_speed_factor = 1 performs much worse than one trained with
    low player_speed_factor, like 0.3, even when running the trained model in environment with player_speed_factor = 1!
    """

    def __init__(self):
        super().__init__()
        self.player_speed_factor = 0.3  # how fast the player moves
        self.flap_state: Literal['flap_more', 'flap_less'] = 'flap_more'
        self.wait_until_next_flap = 3
        self.reset_env()  # reset the environment to apply the player speed factor

    def reset_env(self):
        super().reset_env()
        self.player.set_mode(PlayerMode.TRAIN)
        self.set_player_speed_factor(self.player_speed_factor)
        self.player.set_tick_train(self.tick_player_up_and_down)

    def pick_random_enemy(self):
        self.controlled_enemy_id = random.choice([0, 2]) # control either top or bottom enemy, but not the middle
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

    @staticmethod
    def get_training_config() -> TrainingConfig:
        return TrainingConfig(
            learning_rate=0.0003,
            n_steps=2048,
            batch_size=64,
            gamma=0.99,
            gae_lambda=0.95,
            clip_range=0.1,
            ent_coef=0.005,

            policy_kwargs=dict(
                net_arch=dict(pi=[64, 32], vf=[64, 32]),
                activation_fn=nn.LeakyReLU,
                ortho_init=True,
            ),

            save_freq=40_000,
            total_timesteps=7_000_000,

            normalizer=VecBoxOnlyNormalize,
            clip_norm_obs=5.0,

            frame_stack=-1
        )

    def perform_step(self, action):
        self.step += 1
        for event in pygame.event.get():
            self.handle_quit(event)

        EnemyCloudSkimmerModelController.perform_action(action, self.controlled_enemy)

        self.background.draw()
        self.pipes.tick()
        self.floor.tick()
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

        # set weapon type to a random value, so agent doesn't start ignoring the value as it wouldn't change otherwise
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
            reward -= 0.2

        for bullet in self.all_bullets_from_last_frame.union(self.controlled_enemy.gun.shot_bullets):
            # reward for hitting the player
            if bullet.hit_entity == 'player':
                reward += 5
                # bonus reward if the bullet hit the player after bouncing (trickshot)
                if bullet.bounced:
                    reward += 3
            # punishment for hitting himself or his teammates
            elif bullet.hit_entity == 'enemy':
                reward -= 1
            # (if we punish them for hitting the floor, they get scared of firing down, even if the player is there)
            # punishment for hitting the ground
            # elif bullet.hit_entity == 'floor':
            #     reward -= 0.2
            # reward for hitting a pipe
            elif bullet.hit_entity == 'pipe' and bullet not in self.bullets_bounced_off_pipes:
                self.bullets_bounced_off_pipes.add(bullet)
                reward += 0.1  # was 0.05

        self.all_bullets_from_last_frame = set(self.controlled_enemy.gun.shot_bullets)

        return reward

    def tick_player_up_and_down(self) -> None:
        """
        Move player high up and down randomly, and not just between pipes, like in actual game,
        so agents learn to hit the player and NOT just blindly fire in the center of pipes, no matter where the player is.
        """
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
        else:
            raise ValueError(f"Invalid flap_state: {self.flap_state}")

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

    def set_player_speed_factor(self, speed_factor: float) -> None:
        """
        Set the player's speed factor, which affects how fast the player moves.
        """
        self.player_speed_factor = speed_factor
        self.player.reset_vals_normal()
        self.player.vel_y *= self.player_speed_factor  # player's velocity along Y axis
        self.player.max_vel_y *= self.player_speed_factor  # 18.75  # max vel along Y, max descend speed
        self.player.min_vel_y *= self.player_speed_factor  # min vel along Y, max ascend speed
        self.player.acc_y *= self.player_speed_factor  # players downward acceleration
        self.player.rotation *= self.player_speed_factor  # player's rotation speed
        self.player.vel_rot *= self.player_speed_factor  # player's rotation speed
        self.player.flap_acc *= self.player_speed_factor  # players speed on flapping
