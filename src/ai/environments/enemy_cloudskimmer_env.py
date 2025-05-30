from weakref import WeakSet

import gymnasium as gym
import numpy as np
import pygame
from torch import nn

from src.entities.enemies import CloudSkimmer
from .base_env import BaseEnv
from ..controllers import BasicFlappyModelController, EnemyCloudSkimmerModelController
from ..normalizers.vec_box_only_normalize import VecBoxOnlyNormalize
from ..observations import ObservationManager
from ..training_config import TrainingConfig

"""
Randomly select one of the enemies to control.
Once that enemy dies, terminate the episode and select another one randomly.
"""


# YES, IT SHOULD FLY MORE RANDOMLY!!
# TODO Should the player fly more randomly for a part of training, not just between pipes? So the agents learn some epic
#  bounce tricks to hit the player when he's behind the pipes, instead of just aiming at the player's current position?
#  If we give a higher reward for hitting the player after bouncing off a pipe, the agents try to trick shot the player
#  even when they can directly fire at it, which we don't want. Directly fire at the player when possible, otherwise
#  try a trick shot.

"""
Masking Bullet Data:
During the later stages of training, static placeholder values for bullet info should be introduced.
This step teaches the model to gradually ignore these inputs, which are not critical for decision-making post-training.
It ensures that during deployment, the model can operate effectively even when bullet data is not provided.
"""


class EnemyCloudSkimmerEnv(BaseEnv):
    requires_action_masking = True

    def __init__(self):
        super().__init__()
        self.step: int = 0  # step counter
        self.basic_flappy_controller = BasicFlappyModelController()
        self.observation_manager = ObservationManager()
        self.controlled_enemy_id: int = None  # 0: top, 1: middle, 2: bottom
        self.controlled_enemy: CloudSkimmer = None

        self.pipes.spawn_initial_pipes_like_its_midgame()
        self.spawn_enemies()
        self.pick_random_enemy()
        self.fill_observation_manager()

        # --- stuff needed to calculate the reward ---
        # When the bullet hits the player or an enemy, it gets immediately removed from the gun.shot_bullets set, so we
        # can't see if it hit the player or an enemy, that's why we store references to all bullets from the last frame.
        self.all_bullets_from_last_frame = set()
        self.bullets_bounced_off_pipes = WeakSet()
        self.prev_rotation_action = 0

    def reset_env(self):
        super().reset_env()
        self.step = 0
        self.pipes.spawn_initial_pipes_like_its_midgame()
        self.spawn_enemies()
        self.pick_random_enemy()
        self.fill_observation_manager()

    def spawn_enemies(self):
        self.enemy_manager.spawned_enemy_groups = []
        self.enemy_manager.spawn_cloudskimmer()

    def pick_random_enemy(self):
        self.controlled_enemy_id = np.random.randint(0, 3)
        self.controlled_enemy = self.enemy_manager.spawned_enemy_groups[0].members[self.controlled_enemy_id]

        # reduce the HP of other enemies, so they die sooner, so the agent also learns to play without teammates
        for enemy in self.enemy_manager.spawned_enemy_groups[0].members:
            if enemy != self.controlled_enemy:
                enemy.set_max_hp(90)

    def fill_observation_manager(self):
        self.observation_manager.observation_instances.clear()
        self.observation_manager.create_observation_instance(entity=self.player, env=self)
        self.observation_manager.create_observation_instance(entity=self.controlled_enemy, env=self,
                                                             controlled_enemy_id=self.controlled_enemy_id)

    @staticmethod
    def get_training_config() -> TrainingConfig:
        VERSION: str = "default"  # which training config to use

        match VERSION:  # noqa
            case "default":
                training_config = TrainingConfig(
                    learning_rate=0.0003,
                    n_steps=2048,
                    batch_size=64,
                    gamma=0.99,
                    clip_range=0.2,

                    policy_kwargs=dict(
                        net_arch=dict(pi=[64, 64], vf=[64, 64]),
                        activation_fn=nn.Tanh,
                        ortho_init=True,
                    ),

                    save_freq=80_000,
                    total_timesteps=5_000_000,

                    normalizer=VecBoxOnlyNormalize,
                    clip_norm_obs=10.0,
                )

            case "default":
                training_config = TrainingConfig(
                    learning_rate=0.0003,
                    n_steps=2048,
                    batch_size=64,
                    gamma=0.99,
                    clip_range=0.1,

                    policy_kwargs=dict(
                        net_arch=dict(pi=[64, 64], vf=[64, 64]),
                        activation_fn=nn.LeakyReLU,  # try normal ReLU as well
                        ortho_init=True,
                    ),

                    save_freq=80_000,
                    total_timesteps=5_000_000,

                    normalizer=VecBoxOnlyNormalize,
                    clip_norm_obs=5.0,
                )

            case _:
                raise ValueError(f"Unknown training config version: {VERSION}")

        return training_config

    @staticmethod
    def get_action_and_observation_space() -> tuple[gym.spaces.MultiDiscrete, gym.spaces.Dict]:
        # index 0 -> 0: do nothing, 1: fire, 2: reload
        # index 1 -> 0: do nothing, 1: rotate up, 2: rotate down
        action_space = gym.spaces.MultiDiscrete([3, 3])

        # TODO maybe add remaining_shoot_cooldown and remaining_reload_cooldown to the observation space after all
        #  and punish the agent for attempting to fire or reload when they're on cooldown? Or keep it as it is now?
        observation_space = gym.spaces.Dict({
            'player_y_position': gym.spaces.Box(low=-120, high=755, shape=(1,), dtype=np.float32),
            'player_y_velocity': gym.spaces.Box(low=-17, high=21, shape=(1,), dtype=np.float32),
            # 0: top, 1: middle, 2: bottom; gun type can be derived from this as guns are always in the same order
            'controlled_enemy': gym.spaces.Discrete(3),
            # remaining loaded bullets in the gun
            'remaining_bullets': gym.spaces.Box(low=0, high=30, shape=(1,), dtype=np.float32),
            # this is gun's raw rotation - animation_rotation is not taken into account
            'gun_rotation': gym.spaces.Box(low=-60, high=60, shape=(1,), dtype=np.float32),
            # x position of the controlled enemy
            'enemy_x_position': gym.spaces.Box(low=449, high=1900, shape=(1,), dtype=np.float32),
            # 0: top enemy, 1: middle enemy, 2: bottom enemy (0: doesn't exist, 1: exists)
            'enemy_existence': gym.spaces.MultiBinary(3),
            'top_enemy_y_position': gym.spaces.Box(low=207, high=243, shape=(1,), dtype=np.float32),
            'middle_enemy_y_position': gym.spaces.Box(low=335, high=365, shape=(1,), dtype=np.float32),
            'bottom_enemy_y_position': gym.spaces.Box(low=457, high=493, shape=(1,), dtype=np.float32),
            # x position of vertical center of the first pipe (distance between pipes is always the same)
            'first_pipe_x_position': gym.spaces.Box(low=-265, high=118, shape=(1,), dtype=np.float32),
            # y positions of vertical centers of pipes
            'pipe_y_positions': gym.spaces.Box(low=272, high=528, shape=(4,), dtype=np.float32),
            # 0: b1, 1: b2, 2: b3, 3: b4, ... (0: doesn't exist, 1: exists)
            'bullet_existence': gym.spaces.MultiBinary(10),
            # x and y positions of bullets
            # Up - bullet gets removed off-screen => 0 + max height of bullet = -24 ~ -20 (can't be fired at 90 angle)
            # Down - bullet gets stopped when hitting floor => 797
            # Left - bullet before -256 is useless as it can't bounce back => -256
            # Right - bullet after 1144 is useless as it can't bounce back => 1144 (1144, because that's the first point
            #  where CloudSkimmers can fire from, if the x is larger, that means the bullet bounced and flew past them)
            'bullet_positions': gym.spaces.Box(low=np.array([-256, -20] * 10, dtype=np.float32), high=np.array([1144, 797] * 10, dtype=np.float32), dtype=np.float32)
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
            # self.handle_event(event)  # handles key presses as well
            self.handle_quit(event)

        # here, flappy can get & perform the action before the enemy, as the agent has already decided what it'll do
        self.handle_basic_flappy()

        # print(action[0], self.controlled_enemy.gun.remaining_shoot_cooldown, self.controlled_enemy.gun.remaining_reload_cooldown)
        # Must NOT init EnemyCloudSkimmerModelController(), as it would create a new instance which creates a new
        #  EnemyCloudSkimmerEnv (this), causing infinite recursion. Yeah, really messed up, but it works... for now -_-
        # self.enemy_cloudskimmer_controller.perform_action(self.controlled_enemy, action)
        EnemyCloudSkimmerModelController.perform_action(self.controlled_enemy, action)

        self.update_bullet_info()

        self.background.tick()
        self.pipes.tick()
        self.floor.tick()
        self.player.tick()
        self.enemy_manager.tick()

        pygame.display.update()
        self.config.tick()

        # observation = self.get_state()
        # reward = self.calculate_reward(action=action)
        # print("STEP DONE")
        # print()  # breakpoint here

        # return (observation,
        return (self.get_observation(),  # observation
                # reward,
                self.calculate_reward(action=action),  # reward,
                self.controlled_enemy not in self.enemy_manager.spawned_enemy_groups[0].members,  # terminated
                self.step > 1200,  # truncated; end the episode if it lasts too long
                {})  # info

    def get_observation(self):
        return self.observation_manager.get_observation(self.controlled_enemy)

    def get_action_masks(self) -> np.ndarray:
        # Must NOT init EnemyCloudSkimmerModelController(), as it would create a new instance which creates a new
        #  EnemyCloudSkimmerEnv (this), causing infinite recursion. Yeah, really messed up, but (｡◕‿‿◕｡)
        return EnemyCloudSkimmerModelController.get_action_masks(self.controlled_enemy, self)

    def calculate_reward(self, action) -> int:
        """
        Agent should be rewarded for:
         - hitting/damaging the player (huge reward) + bonus, if the bullet hit the player after bouncing off a pipe
         - hitting a pipe (small reward) - so the likelihood of learning a cool bounce-off-pipe strategy is higher - NONONO, we're gonna do this differently:
            - train the agent in simpler environment at first, with static pipes and static player, hiding behind the pipes at different positions, so they learn trickshots
            - then make player move, but still behind the pipes
            - then make the pipes move
            - finally make the player play normally
         - not firing (small reward each frame the agent doesn't fire, so if he fires but doesn't hit the player, he
           won't get the reward, which is like if he got punished - punishing him if bullet despawns without hitting
           the player might be more logical, however not only is it harder to implement, it might also confuse the
           agent that he was punished after one bullet's position changed to a placeholder)
        Agent should be punished for:
         - hitting himself or his teammates (big punishment)
         - rotating? Maybe a lil tiny punishment if the agent rotates? So it won't rotate unnecessarily...?
           maybe even a slightly bigger punishment for each rotation direction change, so it won't look jittery
        """

        # TODO WARNING! The agent learns to shoot in the middle between the pipes, not actually where the player is.
        #  That's probably because the trained player model flies between the pipes, so the agent has actually never
        #  seen player behind the pipes. We should make the player fly more randomly, not just between pipes!!
        reward = 0

        # reward for not firing
        # if action[0] == 0:
        #     reward += 4
        # or punishment for firing?
        if action[0] == 1:
            reward -= 0.2
        # reward for reloading
        elif action[0] == 2:
            reward += 0.1

        # reward for not rotating
        # if action[1] == 0:
        #     reward += 0.2
        # punishment for rotation direction change
        # if self.prev_rotation_action != action[1]:
        #     self.prev_rotation_action = action[1]
        #     reward -= 0.2

        for bullet in self.all_bullets_from_last_frame.union(self.controlled_enemy.gun.shot_bullets):
            # reward for hitting the player
            if bullet.hit_entity == 'player':
                reward += 2
                # bonus reward if the bullet hit the player after bouncing
                if bullet.bounced:
                    reward += 10
            # punishment for hitting himself or his teammates
            elif bullet.hit_entity == 'enemy':
                reward -= 3
            # reward for hitting a pipe
            elif bullet.hit_entity == 'pipe' and bullet not in self.bullets_bounced_off_pipes:
                self.bullets_bounced_off_pipes.add(bullet)
                reward += 0.4

        self.all_bullets_from_last_frame = set(self.controlled_enemy.gun.shot_bullets)

        if abs(reward) > 2.2:
            print(reward, end=', ')

        return reward

    def handle_basic_flappy(self):
        flappy_observation = self.observation_manager.get_observation(self.player)
        flappy_action = self.basic_flappy_controller.predict_action(flappy_observation, use_action_masks=False)
        self.basic_flappy_controller.perform_action(self.player, flappy_action)
