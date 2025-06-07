import random
from typing import Literal

import numpy as np
import pygame
from torch import nn

from src.ai.controllers import EnemyCloudSkimmerModelController
from src.ai.normalizers.vec_box_only_normalize import VecBoxOnlyNormalize
from src.ai.training_config import TrainingConfig
from src.entities import CloudSkimmer, PlayerMode
from .enemy_cloudskimmer_main_env import EnemyCloudSkimmerEnv
from .enemy_cloudskimmer_step2_env import EnemyCloudSkimmerStep2Env


class EnemyCloudSkimmerStep3Env(EnemyCloudSkimmerStep2Env):
    """
    This environment is the third and last step in training the enemy CloudSkimmer agent.
    It introduces additional mechanics and penalties to refine the agent's behavior.

    Key features:
    - Increased the focus on not hitting teammates or self, by increasing the penalty for doing so.
    - Introduced "normal" player mode. It alternates between previously used "up_down" mode and "normal" mode.
    - Modified the enemy spawn logic - now we spawn anywhere from 1 to 3 enemies at random, to let the agent learn to adapt to different situations.

    Observations:
    After training the agent in this environment, the agent showed greatly reduced (but not fully removed) firing at teammates.
    The agent also, for the most part, forgot how to perform trickshots, which is unfortunate, but not a major issue for the main environment.
    """

    def __init__(self):
        self.flappy_mode: Literal['normal', 'up_down'] = 'up_down'  # current player mode
        self.remaining_mode_duration: int = 0  # how many steps left in the current mode
        self.player_speed_factors = {'normal': 1, 'up_down': 0.5}  # player speed factors for each mode
        super().__init__()  # yeah... this gotta be after setting self.player_speed_factors
        self.reset_env()  # reset the environment to apply the player speed factor and switch to random flappy mode

        self.player_hits_this_episode = 0  # how many times the player was hit by the controlled enemy this episode
        self.teammate_all_hits_this_episode = 0  # how many times the controlled enemy hit its teammates or self this episode
        self.teammate_direct_hits_this_episode = 0  # how many times the controlled enemy hit its teammates directly

    def reset_env(self):
        EnemyCloudSkimmerEnv.reset_env(self)
        self.player.set_mode(PlayerMode.TRAIN)
        self.player.set_tick_train(self.tick_player_alternate_between_normal_and_up_and_down)
        self.switch_flappy_mode(switch_to_mode=random.choice(['normal', 'up_down']))

    def pick_random_enemy(self):
        self.controlled_enemy_id = np.random.randint(0, 3)
        self.controlled_enemy = self.enemy_manager.spawned_enemy_groups[0].members[self.controlled_enemy_id]

        # Remove anywhere from 0 to 2 enemies, but not the controlled one
        num_to_remove = random.choice([0, 1, 2])
        if num_to_remove > 0:
            enemies = [e for e in self.enemy_manager.spawned_enemy_groups[0].members if e.id != self.controlled_enemy_id]
            if len(enemies) >= num_to_remove:
                enemies_to_remove = random.sample(enemies, num_to_remove)
                for enemy in enemies_to_remove:
                    self.enemy_manager.spawned_enemy_groups[0].members.remove(enemy)

        for enemy in self.enemy_manager.spawned_enemy_groups[0].members:  # type: CloudSkimmer
            enemy.set_max_hp(100_000)  # don't let enemies die (you will not spawn all of them every time)

        self.controlled_enemy.gun.shoot_cooldown = 7 if self.controlled_enemy_id != 1 else 20  # make it shoot faster to make rewards less sparse
        self.controlled_enemy.gun.reload_cooldown = 45  # longer reload cooldown than shoot cooldown,
                                                        # but still not too long to make rewards too sparse

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

        # Handle player mode switching
        self.remaining_mode_duration -= 1
        if self.remaining_mode_duration <= 0:
            self.switch_flappy_mode()

        self.background.draw()
        self.pipes.tick()
        self.floor.tick()
        self.player.tick()
        self.enemy_manager.tick()

        pygame.display.update()
        self.config.tick()

        for bullet in self.all_bullets_from_last_frame.union(self.controlled_enemy.gun.shot_bullets):
            if bullet.hit_entity == 'player':
                self.player_hits_this_episode += 1
            elif bullet.hit_entity == 'enemy':
                self.teammate_all_hits_this_episode += 1
                if not bullet.bounced:
                    self.teammate_direct_hits_this_episode += 1

        terminated = self.controlled_enemy not in self.enemy_manager.spawned_enemy_groups[0].members
        truncated = self.step > 1200  # end the episode if it lasts too long

        info = {}
        if terminated or truncated:
            info['hits_player'] = self.player_hits_this_episode
            info['hits_teammate_all'] = self.teammate_all_hits_this_episode
            info['hits_teammate_direct'] = self.teammate_direct_hits_this_episode
            self.player_hits_this_episode = 0
            self.teammate_all_hits_this_episode = 0
            self.teammate_direct_hits_this_episode = 0

        reward = self.calculate_reward(action=action)
        self.all_bullets_from_last_frame = set(self.controlled_enemy.gun.shot_bullets)

        return (
            self.get_observation(),  # observation
            reward,  # reward
            terminated,  # terminated - end the episode if the controlled enemy is dead
            truncated,  # truncated - end the episode if it lasts too long
            info  # info, duh
        )

    def get_observation(self) -> dict[str, np.ndarray]:
        return EnemyCloudSkimmerEnv.get_observation(self)

    def get_action_masks(self) -> np.ndarray:
        return EnemyCloudSkimmerEnv.get_action_masks(self)

    def calculate_reward(self, action) -> int:
        """
        Focus on hitting the target, with a trickshot if necessary.
        Reload in right moments.
        Reduce gun jittering.
        + Don't hit teammates or self.
        """
        reward = 0

        # tiny reward when firing (now that teammates are in the way for longer -> more punishment for reckless firing)
        if action[0] == 1:
            reward += 0.05
        # punishment/reward for reloading depending on how much ammo is left
        if action[0] == 2:
            gun = self.controlled_enemy.gun
            # Check that it is also "< gun.reload_cooldown - 1", because the reload action has already
            # been executed before this method was called, so the reload cooldown is already in progress.
            is_reloading = 0 < gun.remaining_reload_cooldown < gun.reload_cooldown - 1
            # Increase the reward, if you want the agent to reload more often (so it doesn't spam fire as much)
            reward += self.calculate_reload_reward(gun.quantity, gun.magazine_size, is_reloading, (-1, 5))

        # lil punishment for rotation direction change to reduce jittering
        if self.prev_rotation_action != action[1]:
            self.prev_rotation_action = action[1]
            reward -= 0.08

        for bullet in self.all_bullets_from_last_frame.union(self.controlled_enemy.gun.shot_bullets):
            # reward for hitting the player
            if bullet.hit_entity == 'player':
                reward += 5 if self.controlled_enemy_id != 1 else 2  # give smaller reward when middle enemy hits the player
                # bonus reward if the bullet hit the player after bouncing (trickshot)
                if bullet.bounced:
                    reward += 7 if self.controlled_enemy_id != 1 else 3
            # punishment for hitting himself or his teammates
            elif bullet.hit_entity == 'enemy':
                # direct hit (bigger punishment, much easier to predict)
                if not bullet.bounced:
                    reward -= 6
                # bounce hit (smaller punishment, harder to predict)
                else:
                    reward -= 3
            # reward for hitting a pipe
            elif bullet.hit_entity == 'pipe' and bullet not in self.bullets_bounced_off_pipes:
                self.bullets_bounced_off_pipes.add(bullet)
                # punishment if bullet bounces vertically "| |<" off a pipe, before reaching the player x coordinate
                horizontal_distance_to_player = bullet.x - (self.player.x + self.player.w)
                if horizontal_distance_to_player > 0 and bullet.velocity.x > 0:  # bullet is moving towards the enemies (after bouncing)
                    punishment = -(0.6 * (horizontal_distance_to_player / 100)) ** 2  # ranges from roughly -0 to -4, with very rare cases of higher punishment
                    reward += pygame.math.clamp(punishment, -6, 0)
                # reward otherwise
                else:
                    reward += 0.1

        return reward

    def switch_flappy_mode(self, switch_to_mode: Literal['normal', 'up_down'] = None) -> None:
        """
        Switch the player mode between 'normal' and 'up_down'.
        If mode is None, it will switch to the opposite mode currently in use.

        :param switch_to_mode: 'normal' or 'up_down', or None to switch to the opposite mode.
        """
        if switch_to_mode is None:
            switch_to_mode = 'up_down' if self.flappy_mode == 'normal' else 'normal'

        if switch_to_mode not in ['normal', 'up_down']:
            raise ValueError(f"Invalid flappy_mode: {switch_to_mode}. Expected 'normal' or 'up_down'.")

        self.flappy_mode = switch_to_mode
        self.set_player_speed_factor(self.player_speed_factors[switch_to_mode])
        self.remaining_mode_duration = random.randint(400, 600)

    def tick_player_alternate_between_normal_and_up_and_down(self) -> None:
        """
        Tick the player in the current mode.
        In 'normal' mode, the player moves normally.
        In 'up_down' mode, the player flies from top to bottom and back up (within valid bounds).
        """
        if self.flappy_mode == 'normal':
            # normal player movement
            self.handle_basic_flappy()
        elif self.flappy_mode == 'up_down':
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
            raise ValueError(f"Unknown flappy_mode: {self.flappy_mode}")

        self.player.tick_normal()
