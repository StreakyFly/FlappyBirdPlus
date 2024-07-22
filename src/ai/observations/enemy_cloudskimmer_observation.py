import numpy as np
from weakref import WeakKeyDictionary, WeakSet

from .base_observation import BaseObservation
from ...entities.items import Gun


class EnemyCloudSkimmerObservation(BaseObservation):
    def __init__(self, env, use_bullet_info: bool = True):
        super().__init__(env)
        self.use_bullet_info = use_bullet_info

        self.bullet_index_dict = WeakKeyDictionary()  # map bullets to their initial index in the list
        self.replaced_bullets = WeakSet()  # old bullets that were replaced by new ones in the observation space

    def get_observation(self):
        e = self.env
        first_pipe_center_x_position = e.pipes.upper[0].x + e.pipes.upper[0].w // 2
        pipe_center_y_positions = []
        for i, pipe_pair in enumerate(zip(e.pipes.upper, e.pipes.lower)):
            pipe_center = e.get_pipe_pair_center(pipe_pair)
            pipe_center_y_positions.append(pipe_center[1])

        gun: Gun = e.controlled_enemy.gun

        enemy_existence, enemy_y_pos = self.get_enemy_info(e.enemy_manager)
        if self.use_bullet_info:
            bullet_existence, bullet_pos = self.get_bullet_info(gun, e.player)
        else:
            bullet_existence, bullet_pos = [0] * 10, [0, 0] * 10

        game_state = {
            'player_y_position': np.array([e.player.y], dtype=np.float32),
            'player_y_velocity': np.array([e.player.vel_y], dtype=np.float32),
            'controlled_enemy': e.controlled_enemy_id,
            'remaining_bullets': np.array([gun.quantity], dtype=np.float32),
            # this is gun's raw rotation - animation_rotation is not taken into account
            'gun_rotation': np.array([e.controlled_enemy.gun_rotation], dtype=np.float32),
            'enemy_x_position': np.array([e.controlled_enemy.x], dtype=np.float32),
            'enemy_existence': np.array(enemy_existence, dtype=np.float32),
            'top_enemy_y_position': np.array([enemy_y_pos[0]], dtype=np.float32),
            'middle_enemy_y_position': np.array([enemy_y_pos[1]], dtype=np.float32),
            'bottom_enemy_y_position': np.array([enemy_y_pos[2]], dtype=np.float32),
            'first_pipe_x_position': np.array([first_pipe_center_x_position], dtype=np.float32),
            'pipe_y_positions': np.array(pipe_center_y_positions, dtype=np.float32),
            'bullet_existence': np.array(bullet_existence, dtype=np.float32),
            'bullet_positions': np.array(bullet_pos, dtype=np.float32)
        }

        return game_state

    @staticmethod
    def get_enemy_info(enemy_manager):
        enemy_existence = [0] * 3  # flag whether that enemy exists or not
        enemy_y_pos = [0] * 3  # enemy's y position

        for enemy_index, enemy in enumerate(enemy_manager.spawned_enemy_groups[0].members):
            if enemy.is_gone:
                continue
            enemy_existence[enemy_index] = 1
            enemy_y_pos[enemy_index] = enemy.y

        return enemy_existence, enemy_y_pos

    def get_bullet_info(self, gun, player):
        """
        Gets information about bullets fired by the gun.
        The information is stored in two lists, bullet_exists and bullet_positions.
        The list bullet_existence contains flags whether the bullet exists or not.
        The list bullet_positions contains x and y positions (curr_front_pos) of the bullets.
        Bullets should always be put in the same slot in the lists as long as the bullet exist.
        If we have [pos1, pos2, empty_ph, pos4, empty_ph], and the agent fires another bullet,
        we put it in the first empty_ph slot we find. If all slots are filled we replace the oldest bullet.
        If bullet isn't useful, it shouldn't be included. For example if it hit the floor and got stopped.

        :param gun: Gun object that fired the bullets
        :param player: Player object to access its attributes
        :return: List of bullet info (0: does the bullet exist, 1: bullet x position, 2: bullet y position) * 10 bullets
        """

        # 10 bullets max
        bullet_existence = [0] * 10  # flag whether that bullet exists or not
        bullet_pos = [0, 0] * 10  # bullet's x and y position (curr_front_pos)

        new_bullet = None

        # update the array with bullet positions of previously fired bullets (if they still exist)
        for bullet in gun.shot_bullets:
            if not self.is_bullet_info_useful(bullet, player):
                continue

            if bullet not in self.bullet_index_dict:
                if bullet.frame == 0:  # if bullet.frame > 0, it means that bullet's slot was taken by a newer bullet
                    new_bullet = bullet
                continue

            bullet_index = self.bullet_index_dict[bullet]
            bullet_existence[bullet_index] = 1
            bullet_pos[bullet_index * 2] = bullet.curr_front_pos.x  # bullet.x
            bullet_pos[bullet_index * 2 + 1] = bullet.curr_front_pos.y  # bullet.y

        # if a new bullet was fired, put it in the first free slot or replace the oldest bullet if all slots are filled
        if new_bullet:
            try:  # replace the first free slot
                replace_bullet_index = bullet_existence.index(0)
            # (this exception will be thrown very rarely, if ever, as it's very unlikely that all slots are filled)
            except ValueError:  # replace the oldest bullet
                oldest_bullet = None
                oldest_bullet_age = 0
                for bullet in gun.shot_bullets:
                    if not self.is_bullet_info_useful(bullet, player):
                        continue

                    if bullet.frame > oldest_bullet_age and bullet not in self.replaced_bullets:
                        oldest_bullet_age = bullet.frame
                        oldest_bullet = bullet

                self.replaced_bullets.add(oldest_bullet)
                replace_bullet_index = self.bullet_index_dict[oldest_bullet]
                del self.bullet_index_dict[oldest_bullet]

            self.bullet_index_dict[new_bullet] = replace_bullet_index
            bullet_existence[replace_bullet_index] = 1
            bullet_pos[replace_bullet_index * 2] = new_bullet.curr_front_pos.x  # new_bullet.x
            bullet_pos[replace_bullet_index * 2 + 1] = new_bullet.curr_front_pos.y  # new_bullet.y

        return bullet_existence, bullet_pos

    @staticmethod
    def is_bullet_info_useful(bullet, player):
        """
        Checks if the bullet is useful for the observation space.

        Up: bullet is deleted after flying off-screen on top, no need to handle it here
        Down: bullet hit the floor and got stopped
        Right: bullet was flying to the left, bounced back and flew past all the CloudSkimmers to the right
        Left: bullet was flying to the left, bounced off the top/bottom side of pipe and flew past the player to the left
        """
        # down - bullet hit the floor
        if bullet.stopped:
            return False

        # right - bullet flew past CloudSkimmers and can't return
        if bullet.bounced and bullet.x > (max(bullet.enemies, key=lambda enemy: enemy.x).x + bullet.enemies[0].w):
            return False

        # left - bullet flew past the player and can't return
        if bullet.bounced and bullet.velocity.x < 0 and (bullet.x + bullet.w) < player.x:
            return False

        return True
