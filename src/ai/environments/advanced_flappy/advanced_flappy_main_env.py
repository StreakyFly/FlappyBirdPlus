import warnings

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
    [WARN] This environment isn't intended to be used directly for training.
    Use "simpler" environments and train the agent in multiple stages.

    Key features:
    - nothing bruh
    """
    REQUIRES_ACTION_MASKING = True

    def __init__(self):
        super().__init__()
        # self.observation_manager = ObservationManager()
        self.fill_observation_manager()
        self.init_model_controllers(human_player=True)  # True, cuz it shouldn't init player model as we'll be training it

        # Supress these two specific warnings, otherwise it complains we loose precision when working with
        # PLAYER_CX because it's 186.5 (a float64 by default), but float32 is plenty enough to represent it, so
        # instead of wrapping the values in np.float32(x) in every single place, we just supress these two warnings.
        # Hopefully this doesn't backfire ._.
        warnings.filterwarnings("ignore", message=".*Box low's precision lowered by casting to float32, current low.dtype=float64*")
        warnings.filterwarnings("ignore", message=".*Box high's precision lowered by casting to float32, current high.dtype=float64*")

    def reset_env(self):
        super().reset_env()
        self.fill_observation_manager()

    def fill_observation_manager(self):
        self.observation_manager.observation_instances.clear()
        self.observation_manager.create_observation_instance(entity=self.player, env=self)

    @staticmethod
    def get_training_config() -> TrainingConfig:
        return TrainingConfig(
            learning_rate=0.0003,
            n_steps=2048,
            batch_size=256,
            gamma=0.99,
            gae_lambda=0.95,
            clip_range=0.1,
            ent_coef=0.005,

            policy_kwargs=dict(
                net_arch=dict(pi=[64, 32], vf=[64, 32]),  # actor and critic network layers are separate - not shared!
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

        # Player Y position bounds
        PLAYER_CX = self.player.cx
        assert PLAYER_CX == 186.5, (
            f"Expected player.cx to be 186.5 (fixed center-X used for relative observations), "
            f"but got {PLAYER_CX}. If you changed the player's width, "
            f"you must update the observation space bounds accordingly."  # and retrain the agent ._.
        )
        PLAYER_CY_LOW = -90   # Keep in mind low as low value! And NOT position on screen, this is the top of the window.
        PLAYER_CY_HIGH = 785  # Keep in mind high as high value! And NOT position on screen, this is the bottom of the window.

        # Pipe Y positions
        TOP_PIPE_BOTTOM_LOW = 160
        TOP_PIPE_BOTTOM_HIGH = 415
        BOTTOM_PIPE_TOP_LOW = TOP_PIPE_BOTTOM_LOW + self.pipes.vertical_gap
        BOTTOM_PIPE_TOP_HIGH = TOP_PIPE_BOTTOM_HIGH + self.pipes.vertical_gap

        # Relative Y bounds
        TOP_Y_REL_LOW = TOP_PIPE_BOTTOM_LOW - PLAYER_CY_HIGH
        TOP_Y_REL_HIGH = TOP_PIPE_BOTTOM_HIGH - PLAYER_CY_LOW
        BOTTOM_Y_REL_LOW = BOTTOM_PIPE_TOP_LOW - PLAYER_CY_HIGH
        BOTTOM_Y_REL_HIGH = BOTTOM_PIPE_TOP_HIGH - PLAYER_CY_LOW

        # We didn't use any "exists" flags, like we did with the CloudSkimmer observation, because now we pass
        # type/item IDs for almost everything. Valid IDs range from 1 to N. 0 is reserved to indicate that the
        # entity/item does not exist. Meaning adding a separate "exists" flag is redundant.
        observation_space = gym.spaces.Dict({
            'player': gym.spaces.Box(
                low=np.array( [PLAYER_CY_LOW, -17, -90, 0,   0,   0  ], dtype=np.float32),
                high=np.array([PLAYER_CY_HIGH, 21,  20, 100, 100, 100], dtype=np.float32),
                shape=(6,),  # absolute y position, y velocity, rotation, hp, shield, food
                dtype=np.float32
            ),

            'weapon': gym.spaces.Box(
                low=np.array( [15, -45, 0,  0,    0, 0,  0 ], dtype=np.float32),
                high=np.array([80,  90, 28, 9000, 3, 32, 42], dtype=np.float32),
                shape=(7,),  # relative x & y bullet spawn position to player, remaining shoot cooldown, bullets in ammo inventory slot, weapon id, remaining magazine bullets, bullet damage
                dtype=np.float32
            ),

            # We could use discrete space instead of Box for item id and quantity, but let's keep it simple for now.
            # We could also set dtype to np.int16, but np.float32 works just as well and is better supported.
            'inventory': gym.spaces.Box(
                low=np.array([
                    [0, 0, 0],  # slot 3 (food: apple, burger, chocolate)
                    [0, 0, 0],  # slot 4 (potions: shield potion, heal potion)
                    [0, 0, 0]   # slot 5 (heals: bandage, medkit)
                ], dtype=np.float32),
                high=np.array([
                    [3, 100, 60 ],
                    [2, 100, 75 ],
                    [2, 100, 100]
                ], dtype=np.float32),
                shape=(3, 3),  # item id, quantity, value - for each of the 3 slots
                dtype=np.float32
            ),

            # TODO: make sure to spawn a few more items in the training environment,
            #  so there are 3 items on screen at once more frequently.
            # Don't pass quantity in the observation, as the player doesn't see it, so the agent shouldn't either.
            'spawned_items': gym.spaces.Box(
                low=np.full( (3, 4), [0, 0, -100, -900], dtype=np.float32),
                high=np.full((3, 4), [6, 3, 600, 900], dtype=np.float32),
                shape=(3, 4),  # type id, item id, relative x & y position to player
                dtype=np.float32
            ),

            # index 0 -> horizontal distance from player to the next pipe's right-most point
            # index 1 -> vertical distance from player to the next pipe's vertical center
            # index 2 -> vertical distance from player to the second next pipe's vertical center
            'pipes_simple': gym.spaces.Box(
                low=np.array([0, -650, -650], dtype=np.float32),
                high=np.array([500, 550, 550], dtype=np.float32),
                dtype=np.float32
            ),

            # TEMP: the agent might have issues getting past the very first 2-3 pipes, if we only train it with
            #  pipes placed like it's midgame—hopefully not, but adding this comment just in case I forget this and
            #  can't figure out why the agent after getting magnificent results during training is miserably failing
            #  during real-environment testing/evaluation.
            # relative corner positions of the pipes to player (top corners of bottom pipe and bottom corners of top pipe)
            # Do we need to be this specific when defining the low/high values? Probably not, as VecNormalize doesn't
            # even use these values, but let's do it anyway. If we pass an observation that is out of bounds, we'll get
            # an error, which could save us AN ETERNITY of debugging. Does it help with training? Nah, at least not
            # with VecNormalize. Does it help with debugging? Yeah, in some situations it might—by like A LOT.
            # (As long as you set the clip mode to -1!! and NOT 1, as that will just clip it without warning).
            # Last pipe pair is never visible! So we only pass the first 3 pipe pairs.
            'pipes': gym.spaces.Box(
                low=np.array([
                    [  # pipe pair 0
                        [[-330 - PLAYER_CX, TOP_Y_REL_LOW   ], [-200 - PLAYER_CX, TOP_Y_REL_LOW   ]],
                        [[-330 - PLAYER_CX, BOTTOM_Y_REL_LOW], [-200 - PLAYER_CX, BOTTOM_Y_REL_LOW]],
                    ],
                    [  # pipe pair 1
                        [[  60 - PLAYER_CX, TOP_Y_REL_LOW   ], [190 - PLAYER_CX, TOP_Y_REL_LOW   ]],
                        [[  60 - PLAYER_CX, BOTTOM_Y_REL_LOW], [190 - PLAYER_CX, BOTTOM_Y_REL_LOW]],
                    ],
                    [  # pipe pair 2
                        [[ 450 - PLAYER_CX, TOP_Y_REL_LOW   ], [580 - PLAYER_CX, TOP_Y_REL_LOW   ]],
                        [[ 450 - PLAYER_CX, BOTTOM_Y_REL_LOW], [580 - PLAYER_CX, BOTTOM_Y_REL_LOW]],
                    ],
                ]),
                high=np.array([
                    [  # pipe pair 0
                        [[ 60 - PLAYER_CX, TOP_Y_REL_HIGH   ], [190 - PLAYER_CX, TOP_Y_REL_HIGH   ]],
                        [[ 60 - PLAYER_CX, BOTTOM_Y_REL_HIGH], [190 - PLAYER_CX, BOTTOM_Y_REL_HIGH]],
                    ],
                    [  # pipe pair 1
                        [[450 - PLAYER_CX, TOP_Y_REL_HIGH   ], [580 - PLAYER_CX, TOP_Y_REL_HIGH   ]],
                        [[450 - PLAYER_CX, BOTTOM_Y_REL_HIGH], [580 - PLAYER_CX, BOTTOM_Y_REL_HIGH]],
                    ],
                    [  # pipe pair 2
                        [[840 - PLAYER_CX, TOP_Y_REL_HIGH   ], [970 - PLAYER_CX, TOP_Y_REL_HIGH   ]],
                        [[840 - PLAYER_CX, BOTTOM_Y_REL_HIGH], [970 - PLAYER_CX, BOTTOM_Y_REL_HIGH]],
                    ],
                ]),
                shape=(3, 2, 2, 2),
                dtype=np.float32
            ),

            # Don't pass enemy info when it is off-screen, as the agent shouldn't be able to see it!
            #  X position bounds:
            #  - CloudSkimmer: when the front/middle CloudSkimmer peaks on the screen (its gun), at X pos roughly 768,
            #    then you can pass info for all CloudSkimmers, cuz they always form the same formation, so
            #    even though the agent doesn't see the back two yet (at ~858), he could learn that they are there.
            #  - SkyDart: can fly off-screen on the left (< 0), but the moment it flies past the player (< 144), the
            #    agent shouldn't care about it anymore, as it is no longer a threat, but just to make sure it's really
            #    past the player, let's set the low value of the X position to 60 (cuz we'll be passing cx, not x).
            #  Y position bounds: SkyDart can get pretty much anywhere, but if player can't get there, we aren't interested,
            #   so we'll use player's min_y and max_y bounds, plus a solid amount of padding.
            # Rotation: SkyDart might reach rotation just over 80, so let's set the high bound to 87 just in case.
            'enemies': gym.spaces.Box(
                low=np.full( (3, 7), [0,  60-PLAYER_CX, -300-PLAYER_CY_HIGH, -55, -50, -60, 0  ], dtype=np.float32),
                high=np.full((3, 7), [2, 860-PLAYER_CX,  800-PLAYER_CY_LOW ,  0,   80,  87, 100], dtype=np.float32),
                shape=(3, 7),  # 3 enemies, each with: type id, relative x & y position to player, x & y velocity, rotation, hp
                dtype=np.float32
            ),

            # Up - bullet gets removed off-screen => 0 + max height of bullet = -24 ~ -20 (can't be fired at 90 angle)
            # Down - bullet gets stopped when hitting floor at 800, but we'll use 880 just to be safe (if player falls to the floor pushing the gun lower than the 800 floor limit)
            # Left - bullet before -256 is useless as it can't bounce back => -270 just to be safe
            # Right - bullet despawns after 1290, but we'll use 1400 just to be safe (in case bullet has insanely high velocity)
            'bullets': gym.spaces.Box(
                low=np.full( (7, 7), [0, 0, 0, -270-PLAYER_CX, -240-PLAYER_CY_HIGH, -57, -52], dtype=np.float32),
                high=np.full((7, 7), [3, 1, 1, 1400-PLAYER_CX,  880-PLAYER_CY_LOW,   50,  52], dtype=np.float32),
                shape=(7, 7),  # 7 bullets, each with: type id, fired by player flag, bounced flag, relative x & y position to player, x & y velocity
                dtype=np.float32
            )
        })

        return action_space, observation_space

    def get_observation_space_clip_modes(self):
        return {
            'player': -1,
            'weapon': 0,     # print a warning - quantity may go above the high value (very rarely, but possible)
            'inventory': 0,  # print a warning - quantity may go above the high value (very rarely, but possible)
            'spawned_items': 0,  # print a warning - relative y position to player may go out of bounds (very unlikely, but possible)
            'pipes_simple': -1,
            'pipes': 1,      # the pipes are out of bounds at the beginning, so clip them
            'enemies': -1,
            'bullets': -1,
        }

    def perform_step(self, action):
        # Here, other entities can get & perform the action before the agent,
        # as the agent has already decided what it'll do this step.
        self.perform_entity_actions()

        for event in pygame.event.get():
            self.handle_quit(event)
            # self.handle_event(event)  # handles key presses as well  # TODO: comment out when training!
        # self.handle_mouse_buttons()  # handles mouse button presses as well  # TODO: comment out when training!

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
            self.calculate_reward(action=action, died=terminated, passed_pipe=passed_pipe, collected_items=len(collided_items)),  # reward,
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

    def calculate_reward(self, action, died: bool, passed_pipe: bool, collected_items: int) -> float:
        return 0.0
