from weakref import WeakSet

import gymnasium as gym
import numpy as np
import pygame
from torch import nn

from src.ai.controllers import BasicFlappyModelController, EnemyCloudSkimmerModelController
from src.ai.environments.base_env import BaseEnv
from src.ai.normalizers.vec_box_only_normalize import VecBoxOnlyNormalize
from src.ai.observations import ObservationManager
from src.ai.training_config import TrainingConfig
from src.entities.enemies import CloudSkimmer


# TODO ################## [WARN] ####################### [WARN] ####################### [WARN] ######################
#  [WARN]: This environment ended up NOT being directly used for training the latest agent, as the agent learned    #
#  everything I wanted it to learn in the "simpler" environments. However, since those simpler environments INHERIT #
#  from this environment, it will remain in the codebase. I have decided not to merge it with the first inheriting  #
#  environment (enemy_cloudskimmer_step1_env.py), or any other, because the agent is already trained, and I don't   #
#  wanna waste time testing changes that could introduce new bugs (｡◕‿‿◕｡).                                         #
# TODO ###### [WARN] ####################### [WARN] ####################### [WARN] ###################### [WARN] ####


class EnemyCloudSkimmerEnv(BaseEnv):
    """
    [WARN] This environment kinda sucks on its own.
    Use "simpler" environments and train the agent in multiple stages.

    Key features:
    - Randomly select one of the enemies to control.
    - Once that enemy dies, terminate the episode and select another one randomly.
    """
    REQUIRES_ACTION_MASKING = True

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
                enemy.set_max_hp(45)

    def fill_observation_manager(self):
        self.observation_manager.observation_instances.clear()
        # TODO [INFO]: in ObservationManager, you must uncomment `Player: BasicFlappyObservation`,
        #  otherwise it will create the wrong (AdvancedFlappyObservation) observation instance for the player.
        self.observation_manager.create_observation_instance(entity=self.player, env=self)
        self.observation_manager.create_observation_instance(entity=self.controlled_enemy, env=self, controlled_enemy_id=self.controlled_enemy_id)

    @staticmethod
    def get_training_config() -> TrainingConfig:
        VERSION: str = "relu"  # which training config to use

        match VERSION:  # noqa
            case "tanh":
                training_config = TrainingConfig(
                    learning_rate=0.0003,
                    n_steps=2048,
                    batch_size=64,
                    gamma=0.992,
                    gae_lambda=0.954,
                    clip_range=0.2,
                    ent_coef=0.005,

                    policy_kwargs=dict(
                        net_arch=dict(pi=[64, 64], vf=[64, 64]),
                        activation_fn=nn.Tanh,
                        ortho_init=True,
                    ),

                    save_freq=40_000,
                    total_timesteps=7_000_000,

                    normalizer=VecBoxOnlyNormalize,
                    clip_norm_obs=10.0,

                    frame_stack=-1
                )

            case "relu":
                training_config = TrainingConfig(
                    learning_rate=0.0003,
                    n_steps=2048,
                    batch_size=64,
                    gamma=0.99,
                    gae_lambda=0.95,
                    clip_range=0.1,
                    ent_coef=0.005,

                    policy_kwargs=dict(
                        net_arch=dict(pi=[64, 64], vf=[64, 64]),
                        activation_fn=nn.LeakyReLU,
                        ortho_init=True,
                    ),

                    save_freq=40_000,
                    total_timesteps=7_000_000,

                    normalizer=VecBoxOnlyNormalize,
                    clip_norm_obs=5.0,

                    frame_stack=-1
                )

            case "silu":
                training_config = TrainingConfig(
                    learning_rate=0.0003,
                    n_steps=2048,
                    batch_size=64,
                    gamma=0.99,
                    gae_lambda=0.95,
                    clip_range=0.2,
                    ent_coef=0.001,

                    policy_kwargs=dict(
                        net_arch=dict(pi=[64, 64], vf=[64, 64]),
                        activation_fn=nn.SiLU,
                        ortho_init=True,
                    ),

                    save_freq=40_000,
                    total_timesteps=7_000_000,

                    normalizer=VecBoxOnlyNormalize,
                    clip_norm_obs=10.0,

                    frame_stack=-1
                )

            case _:
                raise ValueError(f"Unknown training config version: {VERSION}")

        return training_config

    @staticmethod
    def get_action_and_observation_space() -> tuple[gym.spaces.MultiDiscrete, gym.spaces.Dict]:
        # index 0 -> 0: do nothing, 1: fire, 2: reload
        # index 1 -> 0: do nothing, 1: rotate up, 2: rotate down
        action_space = gym.spaces.MultiDiscrete([3, 3])

        TOP_PIPE_BOTTOM_LOW = 160
        TOP_PIPE_BOTTOM_HIGH = 415
        BOTTOM_PIPE_TOP_LOW = TOP_PIPE_BOTTOM_LOW + 225  # 225 is pipes.vertical_gap
        BOTTOM_PIPE_TOP_HIGH = TOP_PIPE_BOTTOM_HIGH + 225  # 225 is pipes.vertical_gap
        # 'Neural nets tolerate redundancy much better than missing information or brittle assumptions.
        #  Structure and order matter more than minor repetition.' - ChatGPT, 2025
        observation_space = gym.spaces.Dict({
            'enemy_info': gym.spaces.Box(
                low=np.array([
                    [0, 0, 579, 247],  # top enemy (exists, controlled, px, py)
                    [0, 0, 489, 375],  # middle enemy
                    [0, 0, 579, 497],  # bottom enemy
                ], dtype=np.float32),
                high=np.array([
                    [1, 1, 1130, 283],  # top enemy
                    [1, 1, 1040, 405],  # middle enemy
                    [1, 1, 1130, 533],  # bottom enemy
                ], dtype=np.float32),
                shape=(3, 4),  # 3 enemies, each with exists flag, is controlled flag, x and y position, and y velocity
                dtype=np.float32
            ),
            'controlled_enemy_extra_info': gym.spaces.Box(
                # Gun rotation is gun's raw rotation (animation_rotation is not taken into account).
                # Bullet spawn position doesn't have tightly defined bounds, just a rough estimate.
                low=np.array([0, -60, 300, 100, 0], dtype=np.float32),
                high=np.array([1, 60, 1200, 700, 30], dtype=np.float32),
                shape=(5,),  # weapon type, gun rotation, bullet spawn x position, bullet spawn y position, remaining bullets in current magazine
                dtype=np.float32
            ),
            'player_info': gym.spaces.Box(
                #                     py,  vy, rotation
                low=np.array([ -90, -17, -90 ], dtype=np.float32),
                high=np.array([785,  21,  20 ], dtype=np.float32),
                shape=(3,),  # y position, y velocity, rotation
                dtype=np.float32
            ),
            # corner positions of the pipes (top corners of bottom pipe and bottom corners of top pipe)
            # Do we need to be this specific when defining the low/high values? Probably not, as VecNormalize doesn't
            # even use these values, but let's do it anyway. If we pass an observation that is out of bounds, we'll get
            # an error, which could save us AN ETERNITY of debugging. Does it help with training? Nah, at least not
            # with VecNormalize. Does it help with debugging? Yeah, in some situations it might—by like A LOT.
            # (As long as you set the clip mode to -1!! and NOT 1, as that will just clip it without warning).
            'pipe_positions': gym.spaces.Box(
                low=np.array([
                    [  # pipe pair 0
                        [[-330, TOP_PIPE_BOTTOM_LOW], [-200, TOP_PIPE_BOTTOM_LOW]],  # top pipe: left, right
                        [[-330, BOTTOM_PIPE_TOP_LOW], [-200, BOTTOM_PIPE_TOP_LOW]],  # bottom pipe: left, right
                    ],
                    [  # pipe pair 1
                        [[  60, TOP_PIPE_BOTTOM_LOW], [ 190, TOP_PIPE_BOTTOM_LOW]],
                        [[  60, BOTTOM_PIPE_TOP_LOW], [ 190, BOTTOM_PIPE_TOP_LOW]],
                    ],
                    [  # pipe pair 2
                        [[ 450, TOP_PIPE_BOTTOM_LOW], [ 580, TOP_PIPE_BOTTOM_LOW]],
                        [[ 450, BOTTOM_PIPE_TOP_LOW], [ 580, BOTTOM_PIPE_TOP_LOW]],
                    ],
                    [  # pipe pair 3
                        [[ 840, TOP_PIPE_BOTTOM_LOW], [ 970, TOP_PIPE_BOTTOM_LOW]],
                        [[ 840, BOTTOM_PIPE_TOP_LOW], [ 970, BOTTOM_PIPE_TOP_LOW]],
                    ]
                ]),
                high=np.array([
                    [  # pipe pair 0
                        [[  60, TOP_PIPE_BOTTOM_HIGH], [ 190, TOP_PIPE_BOTTOM_HIGH]],
                        [[  60, BOTTOM_PIPE_TOP_HIGH], [ 190, BOTTOM_PIPE_TOP_HIGH]],
                    ],
                    [  # pipe pair 1
                        [[ 450, TOP_PIPE_BOTTOM_HIGH], [ 580, TOP_PIPE_BOTTOM_HIGH]],
                        [[ 450, BOTTOM_PIPE_TOP_HIGH], [ 580, BOTTOM_PIPE_TOP_HIGH]],
                    ],
                    [  # pipe pair 2
                        [[ 840, TOP_PIPE_BOTTOM_HIGH], [ 970, TOP_PIPE_BOTTOM_HIGH]],
                        [[ 840, BOTTOM_PIPE_TOP_HIGH], [ 970, BOTTOM_PIPE_TOP_HIGH]],
                    ],
                    [  # pipe pair 3
                        [[1230, TOP_PIPE_BOTTOM_HIGH], [1360, TOP_PIPE_BOTTOM_HIGH]],
                        [[1230, BOTTOM_PIPE_TOP_HIGH], [1360, BOTTOM_PIPE_TOP_HIGH]],
                    ]
                ]),
                shape=(4, 2, 2, 2),
                dtype=np.float32
            ),
            # Up - bullet gets removed off-screen => 0 + max height of bullet = -24 ~ -20 (can't be fired at 90 angle)
            # Down - bullet gets stopped when hitting floor => 797
            # Left - bullet before -256 is useless as it can't bounce back => -256
            # Right - bullet after 1144 is useless as it can't bounce back => 1144 (1144, because that's the first point
            #  where CloudSkimmers can fire from, if the x is larger, that means the bullet bounced and flew past them)
            'bullet_info': gym.spaces.Box(
                #                                     px,  py,  vx,  vy, bounced
                low=np.full((5, 5), [ -256, -20, -56, -46,  0 ], dtype=np.float32),
                high=np.full((5, 5), [1144, 797,  37,  46,  1 ], dtype=np.float32),
                shape=(5, 5),  # 5 bullets, each with x and y position, x and y velocity, and bounced flag
                dtype=np.float32
            )
        })

        return action_space, observation_space

    @staticmethod
    def get_observation_space_clip_modes() -> dict[str, int]:
        observation_space_clip_modes = {
            'enemy_info': -1,
            'controlled_enemy_extra_info': -1,
            'player_info': -1,
            'pipe_positions': -1,
            'bullet_info': -1,
        }
        return observation_space_clip_modes

    def perform_step(self, action):
        self.step += 1
        for event in pygame.event.get():
            # self.handle_event(event)  # handles key presses as well
            self.handle_quit(event)

        # here, flappy can get & perform the action before the enemy, as the agent has already decided what it'll do
        self.handle_basic_flappy()

        # Must NOT init EnemyCloudSkimmerModelController(), as it would create a new instance which creates a new
        #  EnemyCloudSkimmerEnv (this), causing infinite recursion. Yeah, really messed up, but it works... for now -_-
        # self.enemy_cloudskimmer_controller.perform_action(self.controlled_enemy, action)
        EnemyCloudSkimmerModelController.perform_action(action, self.controlled_enemy)

        self.background.tick()
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
        return self.observation_manager.get_observation(self.controlled_enemy)

    def get_action_masks(self) -> np.ndarray:
        # Must NOT init EnemyCloudSkimmerModelController(), as it would create a new instance which creates a new
        #  EnemyCloudSkimmerEnv (this), causing infinite recursion. Yeah, really messed up, but (｡◕‿‿◕｡)
        return EnemyCloudSkimmerModelController.get_action_masks(self.controlled_enemy, self)

    def calculate_reward(self, action) -> float:
        """
        [WARN] This method was NOT used for training any of the latest/better versions of the agent.
        It is FAR from good—so I should delete it, right?
            Nahh, I'll keep it for reference. I like to look back at my old code and laugh at how dumb I was back then.

        WARNING! The agent learns to shoot in the middle between the pipes, not actually where the player is.
        That's probably because the trained player model flies between the pipes, so the agent has actually never
        seen player behind the pipes. We should make the player fly more randomly, not just between pipes!!

        Agent should be rewarded for:
         - hitting/damaging the player (huge reward) + bonus, if the bullet hit the player after bouncing off a pipe
         - hitting a pipe (small reward) - so the likelihood of learning a cool bounce-off-pipe strategy is higher
         - //not firing (small reward each frame the agent doesn't fire, so if he fires but doesn't hit the player, he
           won't get the reward, which is like if he got punished - punishing him if bullet despawns without hitting
           the player might be more logical, however not only is it harder to implement, it might also confuse the
           agent that he was punished after one bullet's position changed to a placeholder)
        Agent should be punished for:
         - hitting himself or his teammates (big punishment)
         - rotating? Maybe a lil tiny punishment if the agent rotates? So it won't rotate unnecessarily...?
           maybe even a slightly bigger punishment for each rotation direction change, so it won't look jittery
         - firing? Maybe a lil tiny punishment for firing, so it won't fire unnecessarily...?
        """
        reward = 0

        # reward for not firing
        # if action[0] == 0:
        #     reward += 4
        # or punishment for firing?
        if action[0] == 1:
            reward -= 0.08
        # reward for reloading
        elif action[0] == 2:
            reward += 0.04

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
                reward += 5
                # bonus reward if the bullet hit the player after bouncing
                if bullet.bounced:
                    reward += 20
            # punishment for hitting himself or his teammates
            elif bullet.hit_entity == 'enemy':
                reward -= 2
            # reward for hitting a pipe
            elif bullet.hit_entity == 'pipe' and bullet not in self.bullets_bounced_off_pipes:
                self.bullets_bounced_off_pipes.add(bullet)
                reward += 0.2

        self.all_bullets_from_last_frame = set(self.controlled_enemy.gun.shot_bullets)

        return reward

    def handle_basic_flappy(self):
        flappy_observation = self.observation_manager.get_observation(self.player)
        flappy_action = self.basic_flappy_controller.predict_action(flappy_observation, use_action_masks=False)
        self.basic_flappy_controller.perform_action(self.player, flappy_action)
