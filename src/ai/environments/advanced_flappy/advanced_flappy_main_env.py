import gymnasium as gym
import numpy as np
import pygame
from torch import nn

# from src.ai import ObservationManager
from src.ai.controllers.advanced_flappy_controller import AdvancedFlappyModelController
from src.ai.normalizers.vec_box_only_normalize import VecBoxOnlyNormalize
from src.ai.training_config import TrainingConfig
from ..base_env import BaseEnv


# TODO before training the Advanced Flappy Bird agent:
#  4. Finish observations_space in get_action_and_observation_space() method
#  5. Finish advanced_flappy_observation.py, so it returns the correct observation
#  6. Implement proper get_action_masks() method in AdvancedFlappyModelController
#  7. Create a training environment and finally start the training!


class AdvancedFlappyEnv(BaseEnv):
    """
    # TODO: speedrun write this docstring
    """
    REQUIRES_ACTION_MASKING = True

    def __init__(self):
        super().__init__()
        # self.observation_manager = ObservationManager()
        self.fill_observation_manager()
        self.init_model_controllers(human_player=True)

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

        TOP_PIPE_BOTTOM_LOW = 160
        TOP_PIPE_BOTTOM_HIGH = 415
        BOTTOM_PIPE_TOP_LOW = TOP_PIPE_BOTTOM_LOW + self.pipes.vertical_gap
        BOTTOM_PIPE_TOP_HIGH = TOP_PIPE_BOTTOM_HIGH + self.pipes.vertical_gap

        # We didn't use any "exists" flags, like we did with the CloudSkimmer observation, because now we pass
        # type/item IDs for almost everything. Valid IDs range from 1 to N. 0 is reserved to indicate that the
        # entity/item does not exist. Meaning adding a separate "exists" flag is redundant.
        observation_space = gym.spaces.Dict({
            'player': gym.spaces.Box(
                low=np.array( [-90, -17, -90, 0,   0,   0  ], dtype=np.float32),
                high=np.array([785,  21,  20, 100, 100, 100], dtype=np.float32),
                shape=(6,),  # y position, y velocity, rotation, hp, shield, food
                dtype=np.float32
            ),

            'weapon': gym.spaces.Box(
                low=np.array( [205, -114, 0,  0,    0, 0,  0 ], dtype=np.float32),
                high=np.array([262,  874, 28, 9000, 3, 32, 42], dtype=np.float32),
                shape=(7,),  # x & y bullet spawn position, remaining shoot cooldown, bullets in ammo inventory slot, weapon id, remaining magazine bullets, bullet damage
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

            # TODO: spawn a few more items in the training environment, so there are 3 items on screen at once more frequently
            # Don't pass quantity in the observation, as the player doesn't see it, so the agent shouldn't either.
            # If the agent struggles to learn how useful each item is, you could also pass the item value, so for
            # food, potions and heals, we pass fill_value, for weapons, we pass the damage it deals and for
            # ammo_box and token-of-undying, we pass some arbitrary value, like 100. Low/high bounds can be 0-100,
            # unless you change any of the items values beyond that.
            'spawned_items': gym.spaces.Box(
                # X pos: 40-720: spawn_item is 100px wide, player is at pos x 144, so 40+100 is still just past the
                # player. The player can't reach it anymore.
                # Y Pos: -100-800: the item can technically spawn anywhere on the screen, but we won't pass it if it
                # spawns so high/low that the player can't reach it 99.99% of the time without crashing into a pipe.
                low=np.full( (3, 4), [0, 0, 40, -100], dtype=np.float32),
                high=np.full((3, 4), [6, 3, 720, 800], dtype=np.float32),
                shape=(3, 4),  # type id, item id, x & y position
                dtype=np.float32
            ),

            # TEMP: the agent might have issues getting past the very first 2-3 pipes, if we only train it with
            #  pipes placed like it's midgame—hopefully not, but adding this comment just in case I forget this and
            #  can't figure out why the agent after getting magnificent results during training is miserably failing
            #  during real-environment testing/evaluation.
            # corner positions of the pipes (top corners of bottom pipe and bottom corners of top pipe)
            # Do we need to be this specific when defining the low/high values? Probably not, as VecNormalize doesn't
            # even use these values, but let's do it anyway. If we pass an observation that is out of bounds, we'll get
            # an error, which could save us AN ETERNITY of debugging. Does it help with training? Nah, at least not
            # with VecNormalize. Does it help with debugging? Yeah, in some situations it might—by like A LOT.
            # (As long as you set the clip mode to -1!! and NOT 1, as that will just clip it without warning).
            'pipes': gym.spaces.Box(
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
                low=np.full( (3, 7), [0, 60, -300, -55, -50, -60, 0  ], dtype=np.float32),
                high=np.full((3, 7), [2, 860, 800,  0,   80,  87, 100], dtype=np.float32),
                shape=(3, 7),  # 3 enemies, each with: type id, x & y position, x & y velocity, rotation, hp
                dtype=np.float32
            ),

            # Up - bullet gets removed off-screen => 0 + max height of bullet = -24 ~ -20 (can't be fired at 90 angle)
            # Down - bullet gets stopped when hitting floor at 800, but we'll use 880 just to be safe (if player falls to the floor pushing the gun lower than the 800 floor limit)
            # Left - bullet before -256 is useless as it can't bounce back => -270 just to be safe
            # Right - bullet despawns after 1290, but we'll use 1400 just to be safe (in case bullet has insanely high velocity)
            'bullets': gym.spaces.Box(
                low=np.full( (7, 7), [0, 0, 0, -270, -240, -57, -52], dtype=np.float32),
                high=np.full((7, 7), [3, 1, 1, 1400, 880,  50,  52], dtype=np.float32),
                shape=(7, 7),  # 7 bullets, each with: type id, fired by player flag, bounced flag, x & y position, x & y velocity
                dtype=np.float32
            )
        })

        return action_space, observation_space

    def get_observation_space_clip_modes(self):
        return {
            'player': 1, #-1,  # REVERT TO -1
            'weapon': 1,  # 0,     # print a warning - quantity may go above the high value (very unlikely, but possible)  # REVERT TO 0
            'inventory': 0,  # print a warning - quantity may go above the high value (very unlikely, but possible)
            'spawned_items': -1,
            'pipes': 1,      # the pipes are out of bounds at the beginning, so clip them
            'enemies': 1,  #-1,  # REVERT TO -1
            'bullets': -1,
        }

    def perform_step(self, action):
        # Here, other entities can get & perform the action before the agent,
        # as the agent has already decided what it'll do this step.
        # self.handle_basic_flappy()  # TODO: delete this? Why is this even here??
        self.perform_entity_actions()

        for event in pygame.event.get():
            self.handle_quit(event)
            self.handle_event(event)  # handles key presses as well  # TODO: comment out when training!
        self.handle_mouse_buttons()  # handles mouse button presses as well  # TODO: comment out when training!

        # Must NOT init AdvancedFlappyModelController(), as it would create a new instance which creates a new
        #  AdvancedFlappyEnv (this), causing infinite recursion. Yeah, really messed up, but (｡◕‿‿◕｡)
        # AdvancedFlappyModelController.perform_action(action=action, entity=self.player, env=self)

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
        # TODO: reward the agent, if it hits enemies while they are still dangerous - if SkyDart flies past the player,
        #  it's no longer dangerous, the agent shouldn't waste its ammo on it.
        return 0.0
