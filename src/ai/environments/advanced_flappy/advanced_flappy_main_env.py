import gymnasium as gym
import numpy as np
import pygame
from torch import nn

# from src.ai import ObservationManager
from src.ai.controllers.advanced_flappy_controller import AdvancedFlappyModelController
from src.ai.normalizers.vec_box_only_normalize import VecBoxOnlyNormalize
from src.ai.training_config import TrainingConfig
from ..base_env import BaseEnv


class AdvancedFlappyEnv(BaseEnv):
    """
    # TODO: speedrun write this docstring
    """
    requires_action_masking = True

    def __init__(self):
        super().__init__()
        # self.observation_manager = ObservationManager()
        self.fill_observation_manager()

    def reset_env(self):
        super().reset_env()
        self.fill_observation_manager()

    def fill_observation_manager(self):
        self.observation_manager.observation_instances.clear()
        self.observation_manager.create_observation_instance(entity=self.player, env=self)

    @staticmethod
    def get_training_config() -> TrainingConfig:
        # TODO: this worked great for CloudSkimmer, but AdvancedFlappy is a bit
        #  different, so it might need some adjustments
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

    def get_action_and_observation_space(self):
        action_space = gym.spaces.MultiDiscrete([
            2,  # flap (0: nothing, 1: flap)
            3,  # fire/reload (0: nothing, 1: fire, 2: reload)
            4   # use slot (0: nothing, 1: use slot 3, 2: use slot 4, 3: use slot 5)
        ])

        observation_space = gym.spaces.Dict({  # TODO: CHANGE! (placeholder for now)
            'ben': gym.spaces.Box(low=0, high=100, shape=(1,), dtype=np.float32),
            'ten': gym.spaces.Box(low=0, high=100, shape=(1,), dtype=np.float32),
        })

        return action_space, observation_space

    def get_observation_space_clip_modes(self):
        return {
            'ben': 1,
            'ten': 1,
        }

    def perform_step(self, action):
        # Here, other entities can get & perform the action before the agent,
        # as the agent has already decided what it'll do this step.
        # self.handle_basic_flappy()
        # self.perform_entity_actions()

        for event in pygame.event.get():
            # self.handle_event(event)  # handles key presses as well
            # self.handle_mouse_buttons()  # handles mouse button presses as well
            self.handle_quit(event)

        # Must NOT init AdvancedFlappyModelController(), as it would create a new instance which creates a new
        #  AdvancedFlappyEnv (this), causing infinite recursion. Yeah, really messed up, but (｡◕‿‿◕｡)
        AdvancedFlappyModelController.perform_action(action=action, entity=self.player, env=self)

        terminated = False
        passed_pipe = False
        if self.player.crossed(self.next_closest_pipe_pair[0]):
            passed_pipe = True
            self.score.add()
            self.next_closest_pipe_pair = self.get_next_pipe_pair()

        self.player.handle_bad_collisions(self.pipes, self.floor)
        if self.is_player_dead():
            terminated = True

        collided_items = self.player.collided_items(self.item_manager.spawned_items)
        self.item_manager.collect_items(collided_items)

        self.game_tick()

        pygame.display.update()
        self.config.tick()

        return (
            self.get_observation(),  # observation
            self.calculate_reward(action=action),  # reward,
            terminated,  # terminated
            False,  # truncated - end the episode if it lasts too long
            {}  # info
        )

    def get_observation(self):
        return self.observation_manager.get_observation(self.player)

    def get_action_masks(self) -> np.ndarray:
        # Must NOT init AdvancedFlappyModelController(), as it would create a new instance which creates a new
        #  AdvancedFlappyEnv (this), causing infinite recursion. Yeah, really messed up, but (｡◕‿‿◕｡)
        return AdvancedFlappyModelController.get_action_masks(self.player, self)

    def calculate_reward(self, action) -> float:
        return 0.0
