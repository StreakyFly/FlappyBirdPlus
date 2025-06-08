import numpy as np
from torch import nn

from src.ai.normalizers.vec_box_only_normalize import VecBoxOnlyNormalize
from src.ai.training_config import TrainingConfig
from src.entities import CloudSkimmer
from .enemy_cloudskimmer_main_env import EnemyCloudSkimmerEnv
from .enemy_cloudskimmer_step1_env import EnemyCloudSkimmerStep1Env


class EnemyCloudSkimmerStep2Env(EnemyCloudSkimmerStep1Env):
    """
    This environment is the second step in training the enemy CloudSkimmer agent.
    Since the agent has already learned to hit the target directly and with a trickshot,
    this environment aims to teach the agent to control the middle enemy as well,
    reduce gun jittering, and learn when to reload, without forgetting about the trickshots.

    Key features:
    - All three enemies are now controlled by the agent.
    - Reloading is introduced, and the agent is rewarded or punished for reloading.
    - The player movement is slightly faster than in the previous step, however still far slower compared to the main environment.
    """

    def __init__(self):
        super().__init__()
        self.player_speed_factor = 0.4  # how fast the player moves (slight increase from the previous step)
        self.reset_env()  # reset the environment to apply the player speed factor

    def pick_random_enemy(self):
        self.controlled_enemy_id = np.random.randint(0, 3)
        self.controlled_enemy = self.enemy_manager.spawned_enemy_groups[0].members[self.controlled_enemy_id]

        for enemy in self.enemy_manager.spawned_enemy_groups[0].members:  # type: CloudSkimmer
            if enemy.id != self.controlled_enemy_id:
                enemy.set_max_hp(25)  # make other enemies weaker

        self.controlled_enemy.set_max_hp(100_000)  # don't let the controlled enemy die
        self.controlled_enemy.gun.shoot_cooldown = 5 if self.controlled_enemy_id != 1 else 14  # make it shoot faster to make rewards less sparse
        self.controlled_enemy.gun.reload_cooldown = 32  # longer reload cooldown than shoot cooldown,
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

    def get_observation(self) -> dict[str, np.ndarray]:
        return EnemyCloudSkimmerEnv.get_observation(self)

    def get_action_masks(self) -> np.ndarray:
        return EnemyCloudSkimmerEnv.get_action_masks(self)

    def calculate_reward(self, action) -> int:
        """
        Focus on hitting the target, with a trickshot if necessary.
        + Reload in right moments.
        + Reduce gun jittering.
        """
        # if action[0] == 2:
        #     print(f"Enemy {self.controlled_enemy_id} reloaded: {self.controlled_enemy.gun.quantity}/{self.controlled_enemy.gun.magazine_size}")

        reward = 0

        # lil punishment when firing
        if action[0] == 1:
            reward -= 0.2
        # punishment/reward for reloading depending on how much ammo is left
        if action[0] == 2:
            gun = self.controlled_enemy.gun
            # Check that it is also "< gun.reload_cooldown - 1", because the reload action has already
            # been executed before this method was called, so the reload cooldown is already in progress.
            is_reloading = 0 < gun.remaining_reload_cooldown < gun.reload_cooldown - 1
            reward += self.calculate_reload_reward(gun.quantity, gun.magazine_size, is_reloading, (-1, 0.2))

        # tiny punishment for rotation direction change to reduce jittering
        if self.prev_rotation_action != action[1]:
            self.prev_rotation_action = action[1]
            reward -= 0.05

        for bullet in self.all_bullets_from_last_frame.union(self.controlled_enemy.gun.shot_bullets):
            # reward for hitting the player
            if bullet.hit_entity == 'player':
                reward += 5 if self.controlled_enemy_id != 1 else 2  # give smaller reward when middle enemy hits the player
                # bonus reward if the bullet hit the player after bouncing (trickshot)
                if bullet.bounced:
                    reward += 4
            # punishment for hitting himself or his teammates
            elif bullet.hit_entity == 'enemy':
                reward -= 2
            # reward for hitting a pipe
            elif bullet.hit_entity == 'pipe' and bullet not in self.bullets_bounced_off_pipes:
                self.bullets_bounced_off_pipes.add(bullet)
                reward += 0.15

        self.all_bullets_from_last_frame = set(self.controlled_enemy.gun.shot_bullets)

        return reward

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
