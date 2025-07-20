import numpy as np
import pygame
from torch import nn

from src.ai.controllers.advanced_flappy_controller import AdvancedFlappyModelController
from src.ai.normalizers.vec_box_only_normalize import VecBoxOnlyNormalize
from src.ai.training_config import TrainingConfig
from .advanced_flappy_main_env import AdvancedFlappyEnv


class AdvancedFlappyStep1Env(AdvancedFlappyEnv):
    """
    This simplified environment is the first step in training the advanced Flappy agent.
    The agent should learn to fly between the pipes and collect spawned items,
    but shouldn't worry about enemies, how to use items or how to avoid bullets.

    Key features:
    - Items are spawned more frequently and at more random Y positions, to prepare the agent for item drops from killed enemies.
    - The Totem of Undying is not used on death, as that might cause the agent to think it didn't make a fatal mistake.
    """

    def __init__(self):
        super().__init__()

    def reset_env(self):
        super().reset_env()
        self.place_pipes_well()

    @staticmethod
    def get_training_config() -> TrainingConfig:
        VERSION: str = "medium_netarch"  # which training config to use

        match VERSION:  # noqa
            case "small_netarch":
                training_config = TrainingConfig(
                    learning_rate=3e-4,
                    n_steps=2048,
                    batch_size=256,
                    gamma=0.99,
                    gae_lambda=0.96,
                    clip_range=0.1,
                    ent_coef=0.006,
                    vf_coef=0.5,

                    policy_kwargs=dict(
                        net_arch=dict(pi=[64, 32], vf=[64, 32]),
                        activation_fn=nn.LeakyReLU,
                        ortho_init=True,
                    ),

                    save_freq=40_000,
                    total_timesteps=12_000_000,

                    normalizer=VecBoxOnlyNormalize,
                    clip_norm_obs=5.0,

                    frame_stack=-1
                )

            case "medium_netarch":
                training_config = TrainingConfig(
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

                    save_freq=40_000,
                    total_timesteps=12_000_000,

                    normalizer=VecBoxOnlyNormalize,
                    clip_norm_obs=5.0,

                    frame_stack=-1
                )

            case _:
                raise ValueError(f"Unknown training config version: {VERSION}")

        return training_config

    def perform_step(self, action):
        """
        In item_manager.py (ItemManager), in the spawn_item() method, we increased the offset the items can spawn at,
        to prepare the agent for item drops from killed enemies. We used this during training of step1 env:
        y = random.randint(self.last_pipe.y - self.pipes.vertical_gap - 200, self.last_pipe.y - SPAWNED_ITEM_SIZE + 100)
        """
        for event in pygame.event.get():
            self.handle_quit(event)

        # Must NOT init AdvancedFlappyModelController(), as it would create a new instance which creates a new
        #  AdvancedFlappyEnv (this), causing infinite recursion. Yeah, really messed up, but (｡◕‿‿◕｡)
        AdvancedFlappyModelController.perform_action(action=action, entity=self.player, env=self)

        # Don't let the player run out of food
        if self.player.food_bar.current_value <= 20:
            self.player.food_bar.current_value = self.player.food_bar.max_value

        # Spawn items more frequently
        self.item_manager.spawn_cooldown = max(0, self.item_manager.spawn_cooldown - 3)

        terminated = False
        passed_pipe = False
        if self.player.crossed(self.next_closest_pipe_pair[0]):
            passed_pipe = True
            self.score.add()
            self.next_closest_pipe_pair = self.get_next_pipe_pair()

        self.player.handle_bad_collisions(self.pipes, self.floor)
        # if self.is_player_dead():  # Don't call this method, because it'll use TotemOfUndying on death, which we don't want for training.
        if self.player.hp_bar.current_value <= 0:
            terminated = True

        collided_items = self.player.collided_items(self.item_manager.spawned_items)
        self.item_manager.collect_items(collided_items)

        self.background.tick()
        self.pipes.tick()
        self.floor.tick()
        self.item_manager.tick()
        self.player.tick()
        self.inventory.tick()
        self.score.tick()

        pygame.display.update()
        self.config.tick()

        return (
            self.get_observation(),  # observation
            self.calculate_reward(action=action, died=terminated, passed_pipe=passed_pipe, collected_items=len(collided_items)),  # reward,
            terminated,  # terminated
            False,  # truncated - end the episode if it lasts too long
            {}  # info
        )

    def calculate_reward(self, action, died: bool, passed_pipe: bool, collected_items: int) -> float:
        reward = 0

        # huge punishment for dying
        if died:
            reward -= 12
        # lil punishment for flapping
        if action[0] == 1:
            reward -= 0.1
        # medium reward for passing a pipe
        if passed_pipe:
            reward += 2
        # big reward for each collected item
        reward += collected_items * 4

        # lil reward for staying close to the center of the next pipe pair center  <-- don't include this in step2 env!
        for i, pipe in enumerate(self.pipes.upper):
            if pipe.x + pipe.w < self.player.x:
                continue
            else:
                pipe_center_y = self.get_pipe_pair_center((pipe, self.pipes.lower[i]))[1]
                vertical_distance_to_pipe_pair_center = abs(self.player.cy - pipe_center_y)
                if vertical_distance_to_pipe_pair_center < 200:
                    # up to 0.1 reward for being close to the center of the pipe pair
                    reward += 0.1 * (1 - vertical_distance_to_pipe_pair_center / 200)
                break

        return reward

    def place_pipes_well(self) -> None:
        """
        Places the pipes in a way that they don't overlap with the player's X position.
        """
        def are_pipes_well_placed() -> bool:
            for pipe in self.pipes.upper + self.pipes.lower:
                if self.player.x + self.player.w > pipe.x and self.player.x < pipe.x + pipe.w:
                    return False
            return True

        self.pipes.spawn_initial_pipes_like_its_midgame()
        while not are_pipes_well_placed():
            self.pipes.spawn_initial_pipes_like_its_midgame()

        # Move the very next pipe pair on Y axis so the gap center is closer to player's Y position.
        for i, pipe in enumerate(self.pipes.upper):
            if pipe.x + pipe.w < self.player.x:
                continue
            else:
                player_center_y = self.player.cy
                # MUST ASSIGN self.next_closest_pipe_pair AFTER CALLING self.pipes.spawn_initial_pipes_like_its_midgame()
                self.next_closest_pipe_pair = (pipe, self.pipes.lower[i])
                next_pipe_pair_center_y = self.get_pipe_pair_center(self.next_closest_pipe_pair)[1]
                offset = player_center_y - next_pipe_pair_center_y
                random_offset = np.random.randint(-50, -10)
                self.pipes.upper[i].y += offset + random_offset
                self.pipes.lower[i].y += offset + random_offset
                break
