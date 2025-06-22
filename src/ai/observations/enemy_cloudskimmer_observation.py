from weakref import WeakKeyDictionary, WeakSet

import numpy as np

from src.entities.enemies import CloudSkimmer
from src.entities.items import Gun
from src.utils import printc
from .base_observation import BaseObservation


class EnemyCloudSkimmerObservation(BaseObservation):
    def __init__(self, entity: CloudSkimmer, env, controlled_enemy_id: int = None, use_bullet_info: bool = True):
        super().__init__(entity, env)
        self.controlled_enemy_id: int = controlled_enemy_id  # 0: top, 1: middle, 2: bottom
        self.use_bullet_info: bool = use_bullet_info
        self.bullet_info = [[0, 0, 0, 0, 0] for _ in range(5)]

        self.bullet_index_dict = WeakKeyDictionary()  # map bullets to their initial index in the list
        self.replaced_bullets = WeakSet()  # old bullets that were replaced by new ones in the observation space

    def get_observation(self):
        e = self.env

        # pipe_center_positions = [[0, 0] for _ in range(4)]
        # if e.pipes.upper:
        #     pipe_center_positions = []
        #     for i, pipe_pair in enumerate(zip(e.pipes.upper, e.pipes.lower)):
        #         pipe_center = e.get_pipe_pair_center(pipe_pair)
        #         pipe_center_positions.append(pipe_center)

        enemy_info, controlled_enemy_extra_info = self.get_enemy_info(e.enemy_manager, self.controlled_enemy_id)

        #                  py             vy            rotation
        player_info = [e.player.cy, e.player.vel_y, e.player.rotation]

        pipe_corner_positions = self.get_pipe_info()

        if self.use_bullet_info:
            self.bullet_info = self.get_bullet_info(self.entity.gun, e.player)

        game_state = {
            'enemy_info': np.array(enemy_info, dtype=np.float32),
            'controlled_enemy_extra_info': np.array(controlled_enemy_extra_info, dtype=np.float32),
            'player_info': np.array(player_info, dtype=np.float32),
            'pipe_positions': np.array(pipe_corner_positions, dtype=np.float32),
            'bullet_info': np.array(self.bullet_info, dtype=np.float32),
        }

        return game_state

    def get_pipe_info(self):
        pipe_corner_positions = []
        for up_pipe, low_pipe in zip(self.env.pipes.upper, self.env.pipes.lower):
            top_pipe_corners = [
                [up_pipe.x, up_pipe.y + up_pipe.h],  # left bottom corner of top pipe
                [up_pipe.x + up_pipe.w, up_pipe.y + up_pipe.h],  # right bottom corner of top pipe
            ]
            bottom_pipe_corners = [
                [low_pipe.x, low_pipe.y],  # left top corner of bottom pipe
                [low_pipe.x + low_pipe.w, low_pipe.y],  # right top corner of bottom pipe
            ]
            pipe_corner_positions.append([top_pipe_corners, bottom_pipe_corners])

        return pipe_corner_positions

    @staticmethod
    def get_enemy_info(enemy_manager, controlled_enemy_id: int):
        # enemy_pos = [[0, 0]] * 3  # NUH-UH STOP RIGHT THERE BUCKAROO, THIS CREATES THREE REFERENCES TO THE SAME LIST -_-
        # enemy_pos = [[0, 0] for _ in range(3)]  # enemy's x and y position

        placeholder_pos = [[579, 489, 579], [265, 390, 515]]  # cuz 0 is out of observation bounds, so we use these values instead
        #             exists controlled        px                     py
        enemy_info = [[  0,      0,    placeholder_pos[0][i], placeholder_pos[1][i] ] for i in range(3)]  # enemy info for each enemy
        controlled_enemy_extra_info = [
            0,    # weapon type (0: Deagle, 1: AK-47)
            0,    # gun rotation
            500,  # bullet spawn x position (not 0, as that would be out of observation bounds)
            390,  # bullet spawn y position (not 0, as that would be out of observation bounds)
            0,    # bullets remaining in current magazine
        ]

        for enemy in enemy_manager.spawned_enemy_groups[0].members:
            enemy_index = enemy.id
            enemy_info[enemy_index][0] = 1
            enemy_info[enemy_index][1] = int(enemy_index == controlled_enemy_id)
            enemy_info[enemy_index][2] = enemy.cx
            enemy_info[enemy_index][3] = enemy.cy

            if enemy_index == controlled_enemy_id:
                bullet_spawn_position = enemy.gun.calculate_initial_bullet_position()
                controlled_enemy_extra_info[0] = int(controlled_enemy_id != 1)  # (0: Deagle, 1: AK-47)
                controlled_enemy_extra_info[1] = enemy.gun_rotation
                controlled_enemy_extra_info[2] = bullet_spawn_position.x
                controlled_enemy_extra_info[3] = bullet_spawn_position.y
                controlled_enemy_extra_info[4] = enemy.gun.quantity

        return enemy_info, controlled_enemy_extra_info

    def get_bullet_info(self, gun: Gun, player):
        """
        Gets information about bullets fired by the gun.
        Bullets should always be put in the same slot in the lists as long as the bullet exist.
        If we have [pos1, pos2, empty_ph, pos4, empty_ph], and the agent fires another bullet,
        we put it in the first empty_ph slot we find. If all slots are filled we replace the oldest bullet.
        If bullet isn't useful, it shouldn't be included. For example if it hit the floor and got stopped.

        :param gun: Gun object that fired the bullets
        :param player: Player object to access its attributes
        :return: List of bullet info (x, y position, x, y velocity, did bullet already bounce) (5 bullets max, the rest placeholders)
        """

        # 5 bullets max
        bullet_existence = [0] * 5  # flag whether that bullet exists or not
        # bullet_pos = [[0, 0]] * 5  # NUH-UH STOP RIGHT THERE BUCKAROO, THIS CREATES FIVE REFERENCES TO THE SAME LIST -_-
        # bullet_info = [[[0, 0], [0, 0], 0] for _ in range(5)]  # x, y position; x, y velocity; whether the bullet bounced
        #              #px, py, vx, vy, bounced  # "Flat is justice—for the neural net." - ChatGPT 2025
        bullet_info = [[ 0,  0,  0,  0,  0 ] for _ in range(5)]

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
            bullet_info[bullet_index][0] = bullet.curr_front_pos.x  # bullet.x
            bullet_info[bullet_index][1] = bullet.curr_front_pos.y  # bullet.y
            bullet_info[bullet_index][2] = bullet.velocity.x
            bullet_info[bullet_index][3] = bullet.velocity.y
            bullet_info[bullet_index][4] = int(bullet.bounced)

        # if a new bullet was fired, put it in the first free slot or replace the oldest bullet if all slots are filled
        if new_bullet:
            try:  # replace the first free slot
                replace_bullet_index = bullet_existence.index(0)
            # (this exception will be thrown very rarely, if ever, as it's very unlikely that all slots are filled)
            except ValueError:  # replace the oldest bullet
                printc("[WARN] All bullet slots are filled, replacing the oldest bullet.", color="orange")
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
            bullet_info[replace_bullet_index][0] = new_bullet.curr_front_pos.x  # new_bullet.x
            bullet_info[replace_bullet_index][1] = new_bullet.curr_front_pos.y  # new_bullet.y
            bullet_info[replace_bullet_index][2] = new_bullet.velocity.x
            bullet_info[replace_bullet_index][3] = new_bullet.velocity.y
            bullet_info[replace_bullet_index][4] = int(new_bullet.bounced)

        return bullet_info

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
