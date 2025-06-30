from weakref import WeakKeyDictionary, WeakSet

import numpy as np

from src.entities import Player, ItemName, EnemyManager, SpawnedItem
from src.entities.enemies.cloudskimmer import CloudSkimmerGroup, CloudSkimmer
from src.entities.enemies.skydart import SkyDartGroup, SkyDart
from src.entities.inventory import InventorySlot
from src.entities.items import Gun, ItemType, Item
from src.entities.items.food.food import Food
from src.entities.items.heals.heal import Heal
from src.entities.items.item_initializer import ITEM_NAME_TO_CLASS_MAP
from src.entities.items.potions.potion import Potion
# from src.flappybird import FlappyBird
from .base_observation import BaseObservation


class AdvancedFlappyObservation(BaseObservation):
    ITEM_IDS = {
        # Weapons
        ItemName.WEAPON_DEAGLE: 1,
        ItemName.WEAPON_AK47: 2,
        ItemName.WEAPON_UZI: 3,
        # Ammunition
        ItemName.AMMO_BOX: 1,
        # Food
        ItemName.FOOD_APPLE: 1,
        ItemName.FOOD_BURGER: 2,
        ItemName.FOOD_CHOCOLATE: 3,
        # Potions
        ItemName.POTION_HEAL: 1,
        ItemName.POTION_SHIELD: 2,
        # Heals
        ItemName.HEAL_BANDAGE: 1,
        ItemName.HEAL_MEDKIT: 2,
        # Special
        ItemName.TOTEM_OF_UNDYING: 1,
    }
    TYPE_IDS = {
        ItemType.WEAPON: 1,
        ItemType.AMMO: 2,
        ItemType.FOOD: 3,
        ItemType.HEAL: 4,
        ItemType.POTION: 5,
        ItemType.SPECIAL: 6,
    }
    ENEMY_GROUP_IDS = {
        CloudSkimmerGroup: 1,
        SkyDartGroup: 2,
    }
    BULLET_IDS = {
        ItemName.BULLET_BIG: 1,
        ItemName.BULLET_MEDIUM: 2,
        ItemName.BULLET_SMALL: 3,
    }

    def __init__(self, entity: Player, env):
        super().__init__(entity, env)
        # Spawned items
        self.spawned_item_index_dict = WeakKeyDictionary()  # map spawned items to their initial index in the list
        self.ignored_spawned_items = WeakSet()  # "older" spawned items that will no longer be included in the observation
        # Enemies
        self.enemy_index_dict = WeakKeyDictionary()  # map spawned items to their initial index in the list
        # Bullets
        self.bullet_index_dict = WeakKeyDictionary()  # map bullets to their initial index in the list
        self.ignored_bullets = WeakSet()  # bullets that will no longer be included in the observation (because they are no longer a thread)
        self.rightmost_visible_enemy_x: int | None = None  # x position of enemy farthest to the right | None if no enemy on screen

    def get_observation(self):
        e: 'FlappyBird' = self.env  # noqa: F821  # don't import FlappyBird to avoid circular import issues
        # e: FlappyBird = self.env

        # OBS: player
        player: Player = e.player
        player_info = [
            player.cy,  # y position
            player.vel_y,  # y velocity
            player.rotation,  # rotation
            player.hp_bar.current_value,  # hp
            player.shield_bar.current_value,  # shield
            player.food_bar.current_value  # food
        ]

        # OBS: weapon
        gun: Gun = e.inventory.inventory_slots[0].item
        if gun.item_type is ItemType.EMPTY:
            # approximate running mean values for x & y bullet spawn positions, the rest are set to 0
            weapon_info = [240, 410, 0, 0, 0, 0, 0]
        else:
            initial_bullet_pos_x, initial_bullet_pos_y = gun.calculate_initial_bullet_position()
            weapon_info = [
                initial_bullet_pos_x,  # x bullet spawn position
                initial_bullet_pos_y,  # y bullet spawn position
                gun.remaining_shoot_cooldown,  # shoot cooldown
                e.inventory.inventory_slots[1].item.quantity,  # ammo count in inventory
                self.ITEM_IDS[gun.item_name],  # gun id (1 = deagle, 2 = ak47, 3 = uzi)
                gun.quantity,  # remaining magazine bullets
                gun.damage  # bullet damage
            ]

        # OBS: inventory
        inventory_slots: list[InventorySlot] = e.inventory.inventory_slots
        # 3 slots, each with: item id, quantity, value
        inventory_info = [[0, 0, 0], [0, 0, 0], [0, 0, 0]]  # shape (3, 3)
        for i, slot in enumerate(inventory_slots[2:5]):  # only food, potion & heal inventory slots
            spawned_item: (Item | Food | Potion | Heal) = slot.item
            if spawned_item.item_type is not ItemType.EMPTY:
                inventory_info[i] = [
                    self.ITEM_IDS[spawned_item.item_name],  # item id
                    spawned_item.quantity,  # quantity
                    spawned_item.fill_amount  # value
                ]

        # OBS: spawned items
        spawned_items = self.get_spawned_item_info(e)

        # OBS: pipes
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

        # OBS: enemies
        enemy_info = self.get_enemy_info(e)

        # OBS: bullets
        bullet_info = self.get_bullet_info(e)

        game_state = {
            'player': np.array(player_info, dtype=np.float32),
            'weapon': np.array(weapon_info, dtype=np.float32),
            'inventory': np.array(inventory_info, dtype=np.float32),
            'spawned_items': np.array(spawned_items, dtype=np.float32),
            'pipes': np.array(pipe_corner_positions, dtype=np.float32),
            'enemies': np.array(enemy_info, dtype=np.float32),
            'bullets': np.array(bullet_info, dtype=np.float32),
        }

        return game_state

    def get_spawned_item_info(self, e: 'FlappyBird') -> list[list[int]]:  # noqa: F821
        """
        Get spawned item info for the observation.

        It doesn't check for Euclidean distance to the player, which was my initial idea, so we would then pass the
        closest three spawned items, because the issue with that is the distances change every single frame, meaning
        one frame items A, B and C are closer, and the next frame X, Y and Z might be closer, which would confuse the
        heck out of the agent.

        So I decided to simply pass whatever item spawns first and keep it as long as it's relevant.
        In many situations this will mean that that spawned item is the closest to the player, but not always,
        especially not when it comes to enemy item drops, which can appear right in front of the player.
        Considering we'll very rarely have more than 3 items on screen at once, I think I have already complicated
        this far enough and should MOVE THE FUCK ON WHY AM I EVEN WRITING THIS LONG ASS USELESS DOCSTRING????????
        """
        DEFAULT_INFO = [0, 0, 40, 0]
        # 3 items, each with: type id, item id, x & y position
        spawned_items = [DEFAULT_INFO.copy() for _ in range(3)]  # shape (3, 4)

        # get the closest 3 spawned items to the player that are within the screen bounds
        new_items: list[SpawnedItem] = []
        for i, spawned_item in enumerate(e.item_manager.spawned_items):
            if spawned_item in self.ignored_spawned_items:
                continue

            # Start ignoring items that the player will never be able to reach (without almost certainly crashing into a pipe)
            if spawned_item.x < 40 or spawned_item.y < -100 or spawned_item.y > 800:
                self.ignored_spawned_items.add(spawned_item)
                continue

            # Skip items that haven't reached the screen yet
            if spawned_item.x > 720:
                continue

            # If the item is new, add it to the new items list (so it'll be processed later) and continue to the next item
            if spawned_item not in self.spawned_item_index_dict:
                new_items.append(spawned_item)
                continue

            # If we got this far, the item is good to go (was a part of observation before), so simply update its info!
            item_index = self.spawned_item_index_dict[spawned_item]
            spawned_items[item_index] = [
                self.TYPE_IDS[ITEM_NAME_TO_CLASS_MAP[spawned_item.item_name].item_type],  # type id
                self.ITEM_IDS[spawned_item.item_name],  # item id
                spawned_item.x,  # x position
                spawned_item.y,  # y position
            ]

        for new_item in new_items:
            free_item_index = next((i for i, item in enumerate(spawned_items) if item == DEFAULT_INFO), -1)

            if free_item_index == -1:
                # assign the new item to the free slot
                self.spawned_item_index_dict[new_item] = free_item_index
                spawned_items[free_item_index] = [
                    self.TYPE_IDS[ITEM_NAME_TO_CLASS_MAP[new_item.item_name].item_type],  # type id
                    self.ITEM_IDS[new_item.item_name],  # item id
                    new_item.x,  # x position
                    new_item.y,  # y position
                ]
            else:
                # No free slots - we'll just ignore this and all remaining spawned items.
                # We could check if it's closer than any of the current ones, but then they might
                # flicker/alternate between two items, which could cause issues. I'm sure we could
                # somehow solve this as well, but it would have almost no effect cuz this will happen
                # just once every third full moon, so it's just not worth complicating the code for that.
                break

        return spawned_items

    def get_enemy_info(self, e: 'FlappyBird') -> list[list[float]]:  # noqa: F821
        """
        Get enemy info for the observation.

        This works with at most 4 enemies. If you make a new SkyDart formation with over 4 SkyDarts or any other
        type of enemy that can have more than 4 members, you'll need to modify this method to handle that better.
        Currently, it doesn't take into account Euclidean distance to the player, so if there are 4 enemies,
        it might fill the observation with the farthest three and not the closest one. However, this is very unlikely.
        The current SkyDart formations have farther SkyDarts later in the formation list, meaning that
        the fourth SkyDart that is further away from the player will be ignored, until one slot gets freed up.
        """
        DEFAULT_INFO = [0, 530, 300, 0, 0, 0, 0]
        # 3 enemies, each with: type id, x & y position, x & y velocity, rotation, hp
        enemy_info = [DEFAULT_INFO.copy() for _ in range(3)]

        self.rightmost_visible_enemy_x = None  # reset this for every observation

        enemy_manager: EnemyManager = e.enemy_manager
        if enemy_manager.spawned_enemy_groups:
            enemy_type_id = self.ENEMY_GROUP_IDS[type(enemy_manager.spawned_enemy_groups[0])]

            for i, enemy in enumerate(enemy_manager.spawned_enemy_groups[0].members):
                enemy: CloudSkimmer | SkyDart
                # If CloudSkimmer is off-screen, don't include it in the observation.
                if enemy_type_id == 1 and enemy.x > 735:
                    continue
                # If SkyDart is off-screen/past the player, don't include it in the observation.
                if enemy_type_id == 2 and (enemy.cx >= 760 or enemy.cx < 60 or enemy.cy < -220 or enemy.cy > 920):
                    continue

                # `self.rightmost_visible_enemy_x` is not needed for this method, but for `self.is_bullet_info_useful()`
                if self.rightmost_visible_enemy_x is None or enemy.x + enemy.w > self.rightmost_visible_enemy_x:
                    self.rightmost_visible_enemy_x = enemy.x + enemy.w

                # [WARN] This works with AT MOST 4 enemies! You add a fifth one, and you'll have problems.
                # The solution we used for get_spawned_item_info() could work here, even with over 4 enemies,
                # but it's more complex. Because we know there is at most 1 more enemy than the observation can
                # handle and that enemy is *usually* further away than others, I decided to keep it simple and
                # do whatever this is... :thumbs_up:
                if enemy in self.enemy_index_dict:
                    index = self.enemy_index_dict[enemy]
                else:
                    if enemy.id == 3:
                        index = next((i for i, item in enumerate(enemy_info) if item == DEFAULT_INFO), -1)
                        if index == -1:
                            # No free slots - we'll just ignore this enemy and move to the next one.
                            continue
                    else:
                        index = enemy.id
                    self.enemy_index_dict[enemy] = index

                enemy_info[index] = [
                    enemy_type_id,  # type id (1: CloudSkimmer, 2: SkyDart)
                    enemy.cx,  # x position
                    enemy.cy,  # y position
                    enemy.vel_x,  # x velocity
                    enemy.vel_y,  # y velocity
                    enemy.gun_rotation if enemy_type_id == 1 else enemy.rotation,  # rotation (gun rotation for CloudSkimmer, rotation for SkyDart)
                    enemy.hp_bar.current_value  # hp
                ]

        return enemy_info

    def get_bullet_info(self, e: 'FlappyBird') -> list[list[float]]:  # noqa: F821
        """
        Collects and returns information about bullets currently present in the environment for the observation space.

        Handles both player and enemy bullets, prioritizes the most relevant bullets if there are too many,
        and encodes each bullet with type, ownership, bounce status, position, and velocity.
        Returns a fixed-size list of bullet info arrays.
        """
        NUM_BULLETS = 7  # max number of bullets in the observation
        DEFAULT_INFO = [0, 0, 0, 0, 0, 0, 0]
        # `NUM_BULLETS` bullets, each with: type id, fired by player flag, bounced flag, x & y position, x & y velocity
        bullet_info = [DEFAULT_INFO.copy() for _ in range(NUM_BULLETS)]

        all_bullets = []  # list of tuples (bullet instance, fired by player flag)

        # player bullets
        inventory_slot = e.inventory.inventory_slots[0]
        if inventory_slot.item.item_name != ItemName.EMPTY and inventory_slot.item.shot_bullets:
            for bullet_tuple in inventory_slot.item.shot_bullets:
                if self.is_bullet_info_useful(bullet_tuple, e.player):
                    all_bullets.append((bullet_tuple, 1))  # '1' means fired by player
        # enemy bullets
        for group in e.enemy_manager.spawned_enemy_groups:
            if group.members and isinstance(group.members[0], CloudSkimmer):
                for enemy in group.members:
                    for bullet_tuple in enemy.gun.shot_bullets:
                        if self.is_bullet_info_useful(bullet_tuple, e.player):
                            all_bullets.append((bullet_tuple, 0))  # '0' means bullet wasn't fired by player

        dangerous_bullets = []
        if len(all_bullets) > NUM_BULLETS:
            # first filter out bullets that can't hit the player anymore (they might hit enemies, but that's less important for player agent)
            # --> right: bullet flew past the player and can't return
            dangerous_bullets = [
                bullet_tuple for bullet_tuple in all_bullets
                if not (bullet_tuple[0].bounced and bullet_tuple[0].velocity.x > 0 and bullet_tuple[0].x > e.player.x + e.player.w)
            ]
            # if there are still too many bullets, calculate relevance/danger score of each bullet and keep the most relevant ones
            if len(dangerous_bullets) > NUM_BULLETS:
                dangerous_bullets.sort(
                    key=lambda b: self.get_bullet_danger_score(b[0], e.player),
                    reverse=True
                )
                dangerous_bullets = dangerous_bullets[:NUM_BULLETS]

        # use `dangerous_bullets` if there are any (should be either empty or `NUM_BULLETS` of them), otherwise use `all_bullets`
        final_bullets = dangerous_bullets or all_bullets

        # We'll rebuild the `self.bullet_index_dict` with only needed bullets,
        # so we don't have to figure out which bullets we should remove from it.
        # (If a bullet gets replaced by another bullet, and then later becomes more relevant so it would be added again,
        # we'd run into an issue, because the index would already be in the `self.bullet_index_dict`, so we couldn't
        # properly handle it, as there would be multiple bullets assigned to the same index -- so we simply rebuild entire dict).
        prev_bullet_index_dict = self.bullet_index_dict.copy()
        self.bullet_index_dict.clear()

        # Place old bullets in their previous slots
        new_bullets = []
        for bullet_tuple in final_bullets:
            bullet, fired_by_player = bullet_tuple
            if bullet not in prev_bullet_index_dict:
                new_bullets.append(bullet_tuple)
                continue
            index = prev_bullet_index_dict[bullet]
            self.bullet_index_dict[bullet] = index
            bullet_info[index] = [
                self.BULLET_IDS[bullet.item_name],  # type id
                fired_by_player,  # fired by player flag
                int(bullet.bounced),  # bounced flag
                bullet.curr_front_pos.x,  # x position
                bullet.curr_front_pos.y,  # y position
                bullet.velocity.x,  # x velocity
                bullet.velocity.y  # y velocity
            ]

        # Place new bullets in remaining free slots
        last_checked_index = 0  # keep track of the last checked index
        for bullet_tuple in new_bullets:
            for i in range(last_checked_index, len(bullet_info)):
                if bullet_info[i] == DEFAULT_INFO:
                    bullet, fired_by_player = bullet_tuple
                    self.bullet_index_dict[bullet] = i
                    bullet_info[i] = [
                        self.BULLET_IDS[bullet.item_name],  # type id
                        fired_by_player,  # fired by player flag
                        int(bullet.bounced),  # bounced flag
                        bullet.curr_front_pos.x,  # x position
                        bullet.curr_front_pos.y,  # y position
                        bullet.velocity.x,  # x velocity
                        bullet.velocity.y  # y velocity
                    ]
                    last_checked_index = i + 1
                    break

        return bullet_info

    def is_bullet_info_useful(self, bullet, player):
        """
        Checks if the bullet is useful for the observation space.

        UP:     bullet is deleted after flying off-screen on top, no need to handle it here
        DOWN:   bullet hit the floor and got stopped
        RIGHT:  bullet was flying to the right, bounced off the top/bottom side of pipe and flew past all the enemies to the right OR
                bullet was flying to the left, bounced back (off the vertical side of the pipe) and flew past all the enemies to the right
        LEFT:   bullet was flying to the left, bounced off the top/bottom side of pipe and flew past the player to the left OR
                bullet was flying to the right, bounced back (off the vertical side of the pipe) and flew back, past the player to the left
        """
        if bullet in self.ignored_bullets:
            return False

        # down: bullet hit the floor
        if bullet.stopped:
            self.ignored_bullets.add(bullet)
            return False

        # right: bullet flew past visible enemies (enemies at least partially on screen) and can't return (enemy.w should already be included in self.rightmost_visible_enemy_x)
        if bullet.bounced and self.rightmost_visible_enemy_x and bullet.velocity.x > 0 and bullet.x > self.rightmost_visible_enemy_x:
            self.ignored_bullets.add(bullet)
            return False

        # left: bullet flew past the player and can't return
        if bullet.bounced and bullet.velocity.x < 0 and (bullet.x + bullet.w) < player.x:
            self.ignored_bullets.add(bullet)
            return False

        return True

    @staticmethod
    def get_bullet_danger_score(bullet, player) -> float:
        """
        Computes a danger score for a bullet based on how likely and soon it could hit the player.

        The score considers:
        - **Direction**: How well the bullet’s velocity vector aligns with the direction to the player.
        - **Distance**: Closer bullets are more dangerous.
        - **Speed**: Faster bullets are prioritized. However, the close the bullet is, the less important speed is.
        - **Bounce penalty**: Slight reduction if bullet has bounced because now it can't change direction again.

        This score should only be used to decide which bullets are included in the observation
        when too many are present. It should not be passed as part of the agent’s observation space.

        returns: float - value in [0, 1] representing the danger score of the bullet.
        """
        # Vector from bullet to player
        dx = player.cx - bullet.curr_front_pos.x
        dy = player.cy - bullet.curr_front_pos.y

        # Bullet velocity vector
        vx, vy = bullet.velocity.x, bullet.velocity.y
        speed = (vx*vx + vy*vy) ** 0.5
        dist  = (dx*dx + dy*dy) ** 0.5

        # If speed is ~0 this bullet is already stopped (shouldn't happen, but just in case)
        if speed < 1e-5:
            return 0.0

        # Directional alignment (cos θ) (clamped to [0.1,1])
        cos_theta = (vx*dx + vy*dy) / (speed*dist + 1e-5)
        D = max(0.1, cos_theta)  # only forward motion counts

        # Proximity factor (normalized to range [0, 1])
        MAX_DIST = 800.0  # actual max is slightly higher, but realistically never happens
        P = max(0.0, 1.0 - dist / MAX_DIST)

        # Speed factor (normalized to range [0.01, 1.0])
        MIN_SPEED, MAX_SPEED = 20.0, 60.0
        S = max(0.01, min(1.0, (speed - MIN_SPEED) / (MAX_SPEED - MIN_SPEED)))

        # Bounce penalty
        B = 0.96 if bullet.bounced else 1.0

        # Weighted danger score
        ALPHA, BETA, GAMMA = 1.6, 1.0, 0.5  # direction is most important, then proximity, and finally speed
        speed_weight = (1 - P)  # near = 0 (speed doesn't matter), far = 1 (speed matters more)
        weighted_speed = 1.0 - speed_weight * (1.0 - S ** GAMMA)
        return B * (D ** ALPHA) * (P ** BETA) * weighted_speed
