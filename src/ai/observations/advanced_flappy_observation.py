import numpy as np

from src.entities import Player, ItemName, EnemyManager
from src.entities.enemies.cloudskimmer import CloudSkimmerGroup, CloudSkimmer
from src.entities.enemies.skydart import SkyDartGroup, SkyDart
from src.entities.inventory import InventorySlot
from src.entities.items import Gun, ItemType, Item
from src.entities.items.food.food import Food
from src.entities.items.heals.heal import Heal
from src.entities.items.potions.potion import Potion
# from src.flappybird import FlappyBird
from .base_observation import BaseObservation


class AdvancedFlappyObservation(BaseObservation):
    GUN_IDS = {
        ItemName.WEAPON_DEAGLE: 1,
        ItemName.WEAPON_AK47: 2,
        ItemName.WEAPON_UZI: 3,
    }
    ITEM_IDS = {
        ItemName.FOOD_APPLE: 1,
        ItemName.FOOD_BURGER: 2,
        ItemName.FOOD_CHOCOLATE: 3,
        ItemName.HEAL_BANDAGE: 1,
        ItemName.HEAL_MEDKIT: 2,
        ItemName.POTION_HEAL: 1,
        ItemName.POTION_SHIELD: 2,
    }
    ENEMY_GROUP_IDS = {
        CloudSkimmerGroup: 1,
        SkyDartGroup: 2,
    }

    def __init__(self, entity: Player, env):
        super().__init__(entity, env)
        self.enemy_info = [[0, 0, 530, 300, 0, 0, 0, 0] for _ in range(3)]

    def get_observation(self):
        e: 'FlappyBird' = self.env  # type: ignore
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
        if gun.type is ItemType.EMPTY:
            # approximate running mean values for x & y bullet spawn positions, the rest are set to 0
            weapon_info = [240, 410, 0, 0, 0, 0, 0]
        else:
            initial_bullet_pos_x, initial_bullet_pos_y = gun.calculate_initial_bullet_position()
            weapon_info = [
                initial_bullet_pos_x,  # x bullet spawn position
                initial_bullet_pos_y,  # y bullet spawn position
                gun.remaining_shoot_cooldown,  # shoot cooldown
                e.inventory.inventory_slots[1].item.quantity,  # ammo count in inventory
                self.GUN_IDS[gun.name],  # gun id (1 = deagle, 2 = ak47, 3 = uzi)
                gun.quantity,  # remaining magazine bullets
                gun.damage  # bullet damage
            ]

        # OBS: inventory
        inventory_slots: list[InventorySlot] = e.inventory.inventory_slots
        # 3 slots, each with: item id, quantity, value
        inventory_info = [[0, 0, 0], [0, 0, 0], [0, 0, 0]]  # shape (3, 3)
        for i, slot in enumerate(inventory_slots[2:5]):  # only food, potion & heal inventory slots
            item: (Item | Food | Potion | Heal) = slot.item
            if item.type is not ItemType.EMPTY:
                inventory_info[i] = [
                    self.ITEM_IDS[item.name],  # item id
                    item.quantity,  # quantity
                    item.fill_amount
                ]

        # OBS: spawned items
        # TODO yupyup
        # TEMP yupyup
        # TODO yupyup

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
        #  3 enemies, each with: existence, type id, x & y position, x & y velocity, rotation, hp
        enemy_manager: EnemyManager = e.enemy_manager
        if enemy_manager.spawned_enemy_groups:
            enemy_type_id = self.ENEMY_GROUP_IDS[type(enemy_manager.spawned_enemy_groups[0])]
            enemies_on_screen = True
            # If none of the CloudSkimmers are on the screen, don't include them in the observation.
            # If even just one is on the screen, include all of them, cuz they are always in the same formation.
            # SkyDarts are handled later, as we handle each one individually.
            if enemy_type_id == 1 and not(any(enemy.cx < 770 for enemy in enemy_manager.spawned_enemy_groups[0].members)):
                enemies_on_screen = False

            if enemies_on_screen:
                for enemy in enemy_manager.spawned_enemy_groups[0].members:
                    enemy: CloudSkimmer | SkyDart
                    # If SkyDart is off-screen, don't include it in the observation.
                    if enemy_type_id == 2 and (enemy.cx >= 760 or enemy.cx < 60 or enemy.cy < -220 or enemy.cy > 920):
                        continue
                    # TODO: if enemy.id == 3, put it in someone else's observation, once that birb leaves - if it
                    #  doesn't, simply don't include, it so it doesn't error out
                    self.enemy_info[enemy.id] = [
                        1,  # enemy exists
                        enemy_type_id,  # type id (1: CloudSkimmer, 2: SkyDart)
                        enemy.cx,  # x position
                        enemy.cy,  # y position
                        enemy.vel_x,  # x velocity
                        enemy.vel_y,  # y velocity
                        enemy.gun_rotation if enemy_type_id == 1 else enemy.rotation,  # rotation (SkyDart: rotation, CloudSkimmer: gun rotation)
                        enemy.hp_bar.current_value  # hp
                    ]

        # OBS: bullets
        # TODO yupyup
        # TEMP yupyup
        # TODO yupyup

        game_state = {
            'player': np.array(player_info, dtype=np.float32),
            'weapon': np.array(weapon_info, dtype=np.float32),
            'inventory': np.array(inventory_info, dtype=np.float32),
            'spawned_items': np.array([0, 0, 0, 0, 0], dtype=np.float32),
            'pipes': np.array(pipe_corner_positions, dtype=np.float32),
            'enemies': np.array(self.enemy_info, dtype=np.float32),
            'bullets': np.full((15, 7), [0, 0, 0, -256, -20, -56, -46], dtype=np.float32),
        }

        return game_state
