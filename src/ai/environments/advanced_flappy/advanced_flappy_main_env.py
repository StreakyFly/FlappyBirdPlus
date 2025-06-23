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
        BOTTOM_PIPE_TOP_LOW = TOP_PIPE_BOTTOM_LOW + 225  # 225 is pipes.vertical_gap
        BOTTOM_PIPE_TOP_HIGH = TOP_PIPE_BOTTOM_HIGH + 225  # 225 is pipes.vertical_gap

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
            # If the agent struggles to learn how useful each item is, also pass the item value, so for food, potions
            #  and heals, we pass fill_value, for weapons, we pass the damage value and for ammo_box and token-of-undying,
            #  we pass some arbitrary value, like 100. Low/high bounds can be 0-100, unless you change any of the items.
            'spawned_items': gym.spaces.Box(
                low=np.full( (3, 4), [0,   -100,   0, 0], dtype=np.float32),
                high=np.full((3, 4), [720,  900, 6, 3], dtype=np.float32),
                shape=(3, 4),  # x & y position, type id, item id
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
                # TODO: change high bound of Y position, if you make the SkyDart to not crash in the floor (so it turns up and flies up)
                low=np.full( (3, 8), [0, 0, 60, -220, -45, -40, -60, 0  ], dtype=np.float32),
                high=np.full((3, 8), [1, 2, 860, 800,  0,   70,  87, 100], dtype=np.float32),
                shape=(3, 8),  # 3 enemies, each with: existence, type id, x & y position, x & y velocity, rotation, hp
                dtype=np.float32
            ),

            # TODO: bullet info (only relevant ones closer to the player to attempt dodges? and those fired by the player)
            # Up - bullet gets removed off-screen => 0 + max height of bullet = -24 ~ -20 (can't be fired at 90 angle)
            # Down - bullet gets stopped when hitting floor => 797
            # Left - bullet before -256 is useless as it can't bounce back => -256
            # TODO: this value might need to be adjusted now that player bullets are also included!! Increased/reduced?
            #  Possibly 1230, cuz that's where the max left x position of the pipe is? After that, the bullet can't bounce back
            #  But it's VERY unlikely for the bullet to get that far...
            # Right - bullet after 1144 is useless as it can't bounce back => 1144 (1144, because that's the first point
            #  where CloudSkimmers can fire from, if the x is larger, that means the bullet bounced and flew past them)
            'bullets': gym.spaces.Box(
                # TODO y velocity (and possibly also x velocity) might need to be adjusted/increased as player is not limited to firing at -60/60 angle
                low=np.full( (15, 7), [0, 0, 0, -256, -20, -56, -46], dtype=np.float32),
                high=np.full((15, 7), [3, 1, 1, 1144, 797,  37,  46], dtype=np.float32),
                # TODO: 15 is probably overkill, test it and see what's really the max needed, could 10 be enough?
                shape=(15, 7),  # 15 bullets, each with: type id, fired by player flag, bounced flag, x & y position, x & y velocity
                dtype=np.float32
            )
        })

        return action_space, observation_space

    def get_observation_space_clip_modes(self):
        return {
            'player': 1, #-1,  # REVERT TO -1
            'weapon': 0,     # print a warning - quantity may go above the high value (very unlikely, but possible)
            'inventory': 0,  # print a warning - quantity may go above the high value (very unlikely, but possible)
            'spawned_items': -1,
            'pipes': 1,      # the pipes are out of bounds at the beginning, so clip them
            'enemies': -1,
            'bullets': -1,
        }

    def perform_step(self, action):
        # Here, other entities can get & perform the action before the agent,
        # as the agent has already decided what it'll do this step.
        # self.handle_basic_flappy()
        # self.perform_entity_actions()

        for event in pygame.event.get():
            self.handle_event(event)  # handles key presses as well
            # self.handle_mouse_buttons()  # handles mouse button presses as well
            self.handle_quit(event)

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
