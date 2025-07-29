import random
from _weakrefset import WeakSet
from typing import cast

import numpy as np
import pygame
from torch import nn

from src.ai.controllers import AdvancedFlappyModelController
from src.ai.normalizers import VecBoxOnlyNormalize
from src.ai.training_config import TrainingConfig
from src.entities import ItemName, ItemInitializer, EnemyManager, CloudSkimmer, SkyDart
from src.entities.items import Gun
from .advanced_flappy_step1_env import AdvancedFlappyStep1Env


class AdvancedFlappyStep2Env(AdvancedFlappyStep1Env):
    """
    This environment is the second step in training the advanced Flappy agent.
    The agent should learn to fight enemies with weapons while navigating pipes and collecting items.
    The agent is not yet rewarded or punished for using food, potions, or healing items.

    Key features:
    - Enemies spawn randomly. Once one group dies, another immediately spawns.
    - The agent starts each episode with a random weapon and plenty of ammo. It can pick up other weapons during the episode.
    - Gun cooldowns are drastically reduced to make rewards less sparse, so the agent can learn faster.
    - Player's HP is significantly increased to allow for longer training episodes. Colliding with pipes is therefore now punished.
    - Items are spawned more frequently and at more random Y positions, to prepare the agent for item drops from killed enemies.
    - The Totem of Undying is not used on death, as that might cause the agent to think it didn't make a fatal mistake.
    """

    def __init__(self):
        super().__init__()
        self.enemy_manager = TrainingEnemyManager(config=self.config, env=self)
        self.item_initializer = ItemInitializer(config=self.config, env=self, entity=self.player)
        self.handled_enemies = WeakSet()
        self.player_bullets_from_last_frame = set()
        self.enemy_bullets_from_last_frame = set()
        self.prev_gun: Gun = None
        self.curr_observation = None

        # Logging variables
        self.shots_fired_this_episode = 0
        self.enemy_hits_this_episode = 0
        self.self_hits_this_episode = 0

    def reset_env(self):
        super().reset_env()

        # Override the enemy manager with an enemy manager tailored specifically for training
        self.enemy_manager = TrainingEnemyManager(config=self.config, env=self)

        # Give the player a random weapon at the start of each episode
        random_gun_name = random.choice([ItemName.WEAPON_DEAGLE, ItemName.WEAPON_AK47, ItemName.WEAPON_UZI])
        random_gun = cast(Gun, self.item_initializer.init_item(random_gun_name, entity=self.player))
        ammo_item = self.item_initializer.init_item(random_gun.ammo_name, entity=self.player)
        ammo_item.quantity = random_gun.magazine_size * 100  # give the agent plenty of ammo to start with
        random_gun.update_ammo_object(ammo_item)
        self.inventory.inventory_slots[0].item = random_gun
        self.inventory.inventory_slots[1].item = ammo_item

        # Drastically reduce gun's cooldowns (less sparse rewards => faster learning)
        self.reduce_gun_cooldowns(random_gun)
        self.prev_gun = random_gun

        # Increase player's HP
        self.player.hp_bar.max_value = 3000
        self.player.hp_bar.current_value = 3000

    @staticmethod
    def get_training_config() -> TrainingConfig:
        return TrainingConfig(
            learning_rate=3e-4,
            n_steps=2048,
            batch_size=512,
            gamma=0.99,
            gae_lambda=0.96,
            clip_range=0.1,
            ent_coef=0.006,
            vf_coef=0.5,

            policy_kwargs=dict(
                net_arch=dict(pi=[96, 48], vf=[96, 48]),
                activation_fn=nn.LeakyReLU,
                ortho_init=True,
            ),

            save_freq=70_000,
            total_timesteps=15_000_000,

            normalizer=VecBoxOnlyNormalize,
            clip_norm_obs=5.0,

            frame_stack=-1
        )

    def get_observation_space_clip_modes(self):
        clip_modes = super().get_observation_space_clip_modes()
        clip_modes['player'] = 1  # player's HP is over bounds, so clip without warning
        return clip_modes

    def perform_step(self, action):
        """
        In item_manager.py (ItemManager), in the spawn_item() method, we increased the offset the items can spawn at,
        to prepare the agent for item drops from killed enemies. We used this during training of step1 env:
        y = random.randint(self.last_pipe.y - self.pipes.vertical_gap - 200, self.last_pipe.y - SPAWNED_ITEM_SIZE + 100)
        """
        # Here, other entities can get & perform the action before the agent,
        # as the agent has already decided what it'll do this step.
        self.perform_entity_actions()

        for event in pygame.event.get():
            self.handle_quit(event)

        # Must NOT init AdvancedFlappyModelController(), as it would create a new instance which creates a new
        #  AdvancedFlappyEnv (this), causing infinite recursion. Yeah, really messed up, but (｡◕‿‿◕｡)
        AdvancedFlappyModelController.perform_action(action=action, entity=self.player, env=self)

        # Spawn items more frequently (but a lil less frequently than in step1 env, cuz now there'll also be items from enemies)
        self.item_manager.spawn_cooldown = max(0, self.item_manager.spawn_cooldown - 2)

        # Reduce gun's cooldowns
        gun: Gun = self.inventory.inventory_slots[0].item
        if gun != self.prev_gun:
            self.prev_gun = gun
            self.reduce_gun_cooldowns(gun)

        terminated = False
        passed_pipe = False
        if self.player.crossed(self.next_closest_pipe_pair[0]):
            passed_pipe = True
            self.score.add()
            self.next_closest_pipe_pair = self.get_next_pipe_pair()

        self.player.handle_bad_collisions(self.pipes, self.floor)
        # if self.is_player_dead():  # Don't call this method, because it'll use TotemOfUndying on death, which we don't want for training
        if self.player.hp_bar.current_value <= 0:
            terminated = True

        collided_items = self.player.collided_items(self.item_manager.spawned_items)
        self.item_manager.collect_items(collided_items)

        self.game_tick()

        pygame.display.update()
        self.config.tick()

        # We update logging variables in `calculate_reward()` method
        enemy_hit_rate_this_episode = self.enemy_hits_this_episode / max(1, self.shots_fired_this_episode)
        self_hit_rate_this_episode = self.self_hits_this_episode / max(1, self.shots_fired_this_episode)

        info = {}
        if terminated:
            info['shots_fired'] = self.shots_fired_this_episode
            info['enemy_hit_rate'] = enemy_hit_rate_this_episode
            info['self_hit_rate'] = self_hit_rate_this_episode
            self.shots_fired_this_episode = 0
            self.enemy_hits_this_episode = 0
            self.self_hits_this_episode = 0

        self.curr_observation = self.get_observation()

        return (
            self.curr_observation,  # observation, duh
            self.calculate_reward(action=action, died=terminated, passed_pipe=passed_pipe, collected_items=len(collided_items)),  # reward,
            terminated,  # terminated - end the episode if the player dies
            False,  # truncated - end the episode if it lasts too long
            info  # info, duh
        )

    def calculate_reward(self, action, died: bool, passed_pipe: bool, collected_items: int) -> float:
        """
        Rewards and punishments:
        - Dying: huge punishment.
        - Colliding with pipes: huge-ish punishment.
        - Firing the gun: small punishment, with extra if no enemies are visible.
        - Reloading: punishment/reward depending on how much ammo is left and if enemies are present.
        - Passing a pipe: medium reward.
        - Collecting items: big reward per item.
        - Getting hit by bullets: small punishment for enemy bullets, medium for self-inflicted hits.
        - Hitting enemies: medium reward, with extra for trickshots.
        - Killing enemies: big reward.
        - Dodging SkyDarts: medium reward.
        - Getting hit by SkyDarts: big punishment.
        - Staying near the pipe center (well, slightly below, because the player died by hitting the upper pipe way too often): small reward.
        """
        reward = 0

        # huge punishment for dying
        if died:
            reward -= 12
        # huge-ish punishment for colliding with pipes (because it would die if it didn't have buffed HP for training)
        for pipe in self.pipes.upper + self.pipes.lower:
            if self.player.collide(pipe):
                reward -= 9
                break

        DEFAULT_INFO = [0, 530, 300, 0, 0, 0, 0]  # [WARN]: If you change DEFAULT_INFO in `advanced_flappy_observation.py`, change it here as well!
        enemy_visible = np.any(self.curr_observation['enemies'] != DEFAULT_INFO)

        # small punishment for firing the gun
        if action[1] == 1:
            reward -= 0.5
            # extra punishment if enemies aren't visible on screen (aren't a part of the observation)
            if not enemy_visible:
                reward -= 4

        # keep track of how many shots were fired by the player
        gun: Gun = self.inventory.inventory_slots[0].item
        self.shots_fired_this_episode += len(gun.shot_bullets - self.player_bullets_from_last_frame)

        # punishment/reward for reloading depending on how much ammo is left and if enemies are present
        if action[1] == 2:
            if enemy_visible:
                # Check that it is also "< gun.reload_cooldown - 1", because the reload action has already
                # been executed before this method was called, so the reload cooldown is already in progress.
                is_reloading = 0 < gun.remaining_reload_cooldown < gun.reload_cooldown - 1
                reward += self.calculate_reload_reward(gun.quantity, gun.magazine_size, is_reloading, (-3, 0.7))
            else:
                # medium reward for reloading when no enemies are visible
                reward += 2  # this reward must be LOWER than the total punishment for firing a single bullet, so that the agent doesn't spam reload

        # medium reward for passing a pipe
        if passed_pipe:
            reward += 2
        # big reward for each collected item
        reward += collected_items * 6.4

        # small punishment for getting hit by enemy's bullet -- small punishment because it's hard to avoid
        for bullet in self.enemy_bullets_from_last_frame:
            if bullet.hit_entity == 'player':
                reward -= 0.4

        for bullet in self.player_bullets_from_last_frame:
            # medium punishment for getting hit by its own bullet -- bigger punishment because umm DON'T SHOOT YOURSELF
            if bullet.hit_entity == 'player':
                self.self_hits_this_episode += 1
                reward -= 2
            # reward for hitting enemies
            elif bullet.hit_entity == 'enemy':
                self.enemy_hits_this_episode += 1
                reward += 2
                # medium reward for hitting enemies
                if bullet.bounced:
                    # extra reward for hitting enemies after bouncing (trickshot)
                    reward += 3.4

        self.player_bullets_from_last_frame = set(gun.shot_bullets)
        self.enemy_bullets_from_last_frame = set()

        enemy_groups = self.enemy_manager.spawned_enemy_groups
        for enemy in enemy_groups[0].members if enemy_groups else []:
            # fill the enemy_bullets_from_last_frame set with current bullets to prepare for the next frame
            if isinstance(enemy, CloudSkimmer):
                self.enemy_bullets_from_last_frame.update(enemy.gun.shot_bullets)
            if enemy in self.handled_enemies:
                continue
            # big reward for killing enemies
            if enemy.hp_bar.current_value <= 0:
                self.handled_enemies.add(enemy)
                reward += 7
            elif isinstance(enemy, SkyDart):
                # big punishment for getting hit by a SkyDart -- big punishment because agent can kill them to avoid getting hit
                if enemy.damaged_target:
                    self.handled_enemies.add(enemy)
                    reward -= 6
                # medium reward for dodging a SkyDart (killing them is better, but dodging also works)
                elif enemy.x + enemy.w < self.player.x:
                    self.handled_enemies.add(enemy)
                    reward += 4

        # lil reward for staying close to the vertical center of the next pipe pair (slightly lower than center)
        for i, pipe in enumerate(self.pipes.upper):
            if pipe.x + pipe.w < self.player.x:
                continue
            else:
                pipe_center_y = self.get_pipe_pair_center((pipe, self.pipes.lower[i]))[1]
                # vertical_distance_to_pipe_pair_center = abs(self.player.cy - pipe_center_y)
                vertical_distance_to_pipe_pair_center = abs(self.player.cy - (pipe_center_y + 20))  # slightly lower than center
                if vertical_distance_to_pipe_pair_center < 200:
                    # up to 0.2 reward for being close to the center of the pipe pair
                    reward += 0.2 * (1 - vertical_distance_to_pipe_pair_center / 200)
                break

        return reward

    @staticmethod
    def reduce_gun_cooldowns(gun: Gun):
        gun.shoot_cooldown = max(1, gun.shoot_cooldown // 6)  # ak47 & uzi end up with 1 frame cooldown, deagle with 4 frames
        gun.reload_cooldown = max(1, gun.reload_cooldown // 9)  # roughly 6-9 frames cooldown for all guns

    @staticmethod
    def calculate_reload_reward(curr_quantity: int, magazine_size: int, is_reloading: bool, reward_bounds: tuple[float, float] = (-1, 0.2)) -> float:
        """
        Calculate the reload punishment or reward based on current ammo.

        Returns a (large) negative reward for reloading at high ammo,
        and a (small) positive reward for reloading at very low ammo,
        using a smooth non-linear decay curve.

        :param curr_quantity: Current ammo quantity.
        :param magazine_size: Maximum magazine size.
        :param is_reloading: Whether the gun is currently reloading.
        :param reward_bounds: Tuple of (min_reward, max_reward) for the reload reward.
        :return: Reward for reloading based on current ammo quantity.
        """
        # Return 0 if the gun is currently reloading, so the agent doesn't farm rewards by trying to reload if it's
        # currently reloading. This shouldn't be even possible, thanks to action masks, but just in case.
        if is_reloading:
            return 0

        # Normalize ammo quantity to range [0, 1]
        normalized_quantity = curr_quantity / magazine_size

        # Smooth punishment/reward curve: from -1 (full) to +0.2 (empty)
        # reward = -1 + 1.2 * (1 - normalized_quantity ** 1.4)
        reward = reward_bounds[0] + (reward_bounds[1] - reward_bounds[0]) * (1 - normalized_quantity ** 1.4)

        return reward

class TrainingEnemyManager(EnemyManager):
    """
    Spawn a new random enemy group immediately after the previous one is killed.
    """
    def can_spawn_enemy(self) -> bool:
        return not self.spawned_enemy_groups

    def spawn_enemy(self) -> None:
        if random.random() < 0.5:
            self.spawn_cloudskimmer()
        else:
            self.spawn_skydart()
