import random

import numpy as np
import pygame

from src.ai.controllers import EnemyCloudSkimmerModelController
from src.ai.environments.enemy_cloudskimmer.enemy_cloudskimmer_main_env import EnemyCloudSkimmerEnv
from src.entities import PlayerMode, CloudSkimmer

"""
TODO: write this comment better, but like
A simpler environment compared to main_env.py, cuz pipes and player won't move, so agents
can first learn that they have to hit the target and how to hit trickshots
which should be much simpler to figure out when the target and the rest of the env isn't moving

The target should be static, but can move every 5 seconds or so, to different position, so
it doesn't overfit to one position. Same with the pipes.

TODO: maybe constantly move the player up and down? At different speeds? Cuz teleporting might be confusing.
"""


class EnemyCloudSkimmerStaticEnv(EnemyCloudSkimmerEnv):
    def __init__(self):
        super().__init__()
        self.reset_env()

    def reset_env(self):
        super().reset_env()
        self.player.set_mode(PlayerMode.TRAIN)
        self.player.set_tick_train(self.tick_player_random_positions)
        self.place_pipes_well()

    def spawn_enemies(self):
        self.enemy_manager.spawned_enemy_groups = []
        self.enemy_manager.spawn_cloudskimmer()
        for enemy in self.enemy_manager.spawned_enemy_groups[0].members:  # type: CloudSkimmer
            enemy.hp_manager.set_value(1_000_000)  # don't let the enemy die
            enemy.gun.reload_cooldown = enemy.gun.shoot_cooldown

    def perform_step(self, action):
        self.step += 1
        for event in pygame.event.get():
            self.handle_quit(event)

        # spawn new randomly positioned pipes every 450 ticks
        if self.step % 450 == 0:
            self.pipes.spawn_initial_pipes_like_its_midgame()
            self.place_pipes_well()

        EnemyCloudSkimmerModelController.perform_action(self.controlled_enemy, action)

        self.update_bullet_info()

        self.background.draw()
        self.pipes.draw()
        self.floor.draw()
        self.player.tick()
        self.enemy_manager.tick()

        pygame.display.update()
        self.config.tick()

        return (
            self.get_observation(),  # observation
            self.calculate_reward(action=action),  # reward,
            self.controlled_enemy not in self.enemy_manager.spawned_enemy_groups[0].members,  # terminated
            self.step > 1200,  # truncated; end the episode if it lasts too long
            {}  # info
        )

    def get_observation(self) -> dict[str, np.ndarray]:
        # TODO: we might want to overwrite this? So it replaces some real values with placeholder values
        #  to make the environment easier to learn.
        #  Or can we keep it as it is? In that case, simply delete this method here.
        obs = super().get_observation()

        return obs

    def get_action_masks(self) -> np.ndarray:
        action_masks = super().get_action_masks()

        # don't let the agent reload (yet)
        action_masks[0][2] = 0

        return action_masks

    def calculate_reward(self, action) -> int:
        """
        Focus on hitting the target, ideally with a trickshot.
        """
        reward = 0

        # lil punishment when firing
        if action[0] == 1:
            reward -= 0.05

        for bullet in self.all_bullets_from_last_frame.union(self.controlled_enemy.gun.shot_bullets):
            # reward for hitting the player
            if bullet.hit_entity == 'player':
                reward += 1
                # bonus reward if the bullet hit the player after bouncing
                if bullet.bounced:
                    reward += 5
            # punishment for hitting himself or his teammates
            elif bullet.hit_entity == 'enemy':
                reward -= 0.3
            # reward for hitting a pipe
            # elif bullet.hit_entity == 'pipe' and bullet not in self.bullets_bounced_off_pipes:
            #     self.bullets_bounced_off_pipes.add(bullet)
            #     reward += 0.2

        self.all_bullets_from_last_frame = set(self.controlled_enemy.gun.shot_bullets)

        return reward

    def tick_player_random_positions(self) -> None:
        # move player to random y position every 150 steps
        if self.step % 150 == 0:
            self.player.y = np.random.randint(self.player.min_y, self.player.max_y)
            self.player.rotation = random.randint(-90, 20)

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
