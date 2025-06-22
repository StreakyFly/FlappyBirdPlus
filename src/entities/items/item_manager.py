import random
from typing import List

import pygame

from src.utils import GameConfig
from .item import SpawnedItem
from .item_enums import ItemName
from .item_spawn_chances import get_spawn_chances


class ItemManager:
    def __init__(self, config: GameConfig, inventory, pipes):
        self.config = config
        self.inventory = inventory
        self.pipes = pipes
        self.spawned_items: List[SpawnedItem] = []
        self.spawn_cooldown: int = 150  # self.config.fps * 5 <-- we don't want it tied to the fps
        self.stopped = False
        # self.count = 0  # TODO delete
        self.first_items_to_spawn = [[ItemName.WEAPON_AK47, ItemName.WEAPON_DEAGLE, ItemName.WEAPON_UZI],
                                     [ItemName.POTION_HEAL, ItemName.POTION_SHIELD],
                                     [ItemName.WEAPON_AK47, ItemName.WEAPON_DEAGLE, ItemName.WEAPON_UZI],
                                     [ItemName.HEAL_MEDKIT, ItemName.HEAL_BANDAGE]]

    def tick(self) -> None:
        for item in self.spawned_items:
            item.tick()

        if self.stopped:
            return

        # self.count += 1  # TODO: delete
        # if 70 < self.count < 90:  # TODO: delete
        #     self.spawned_items.append(SpawnedItem(config=self.config, item_name=ItemName.POTION_SHIELD,
        #                                x=800, y=700, image=self.config.images.item_spawn_bubble))
        #     self.spawned_items.append(SpawnedItem(config=self.config, item_name=ItemName.POTION_HEAL,
        #                                x=800, y=600, image=self.config.images.item_spawn_bubble))
        #     self.spawned_items.append(SpawnedItem(config=self.config, item_name=ItemName.TOTEM_OF_UNDYING,
        #                                x=800, y=500, image=self.config.images.item_spawn_bubble))
        #     self.spawned_items.append(SpawnedItem(config=self.config, item_name=ItemName.POTION_HEAL,
        #                                x=800, y=400, image=self.config.images.item_spawn_bubble))
        #     self.spawned_items.append(SpawnedItem(config=self.config, item_name=ItemName.POTION_SHIELD,
        #                                x=800, y=300, image=self.config.images.item_spawn_bubble))
        #     self.spawned_items.append(SpawnedItem(config=self.config, item_name=ItemName.TOTEM_OF_UNDYING,
        #                                x=800, y=200, image=self.config.images.item_spawn_bubble))
        #     self.spawned_items.append(SpawnedItem(config=self.config, item_name=ItemName.POTION_SHIELD,
        #                                x=800, y=100, image=self.config.images.item_spawn_bubble))
        #     self.spawned_items.append(SpawnedItem(config=self.config, item_name=ItemName.POTION_HEAL,
        #                                x=800, y=0, image=self.config.images.item_spawn_bubble))

        # items = [ItemName.WEAPON_AK47, ItemName.WEAPON_DEAGLE, ItemName.WEAPON_UZI, ItemName.AMMO_BOX,
        #          ItemName.POTION_HEAL, ItemName.POTION_SHIELD, ItemName.TOTEM_OF_UNDYING]
        # for i in range(16):
        #     item_name = random.choice(items)
        #     self.spawned_items.append(SpawnedItem(config=self.config, item_name=item_name,
        #                               x=800, y=50*i, image=self.config.images.item_spawn_bubble))
        # print(len(self.spawned_items))

        if self.can_spawn_item():
            self.spawn_item()

        self.despawn_items()

    def stop(self) -> None:
        self.stopped = True
        for item in self.spawned_items:
            item.stop()

    def can_spawn_item(self) -> bool:
        self.last_pipe = self.pipes.lower[-1]
        # return True

        if self.spawn_cooldown > 0:
            self.spawn_cooldown -= 1
            return False

        self.spawn_cooldown = random.randint(60, 150)  # 2-5 seconds if fps is 30
        return True

    def spawn_item(self, spawn_pos: pygame.Vector2 = None, should_center: list[bool] = None, possible_items: list[ItemName] = None) -> None:
        item_name: ItemName = None  # noqa
        if possible_items is not None:
            item_name = self.get_random_spawn_item(possible_items)
        elif self.first_items_to_spawn:
            item_name = random.choice(self.first_items_to_spawn.pop(0))
        else:
            item_name = self.get_random_spawn_item()

        # TODO further improve spawn position - calculate where the player will be able to collect the spawned
        #  item, and then adjust the spawn position accordingly, so that the player can collect the item and it doesn't
        #  end within the pipe when it reaches the player. Basically reverse calculate the position where the item
        #  should be spawned (take into account the amplitude and frequency of the spawned item).
        if spawn_pos is not None:
            SPAWNED_ITEM_HALF_SIZE = 50  # half of the size of the spawned item bubble (100x100; self.config.images.item_spawn_bubble)
            # subtract half the size of the spawned item bubble from the spawn position to center it
            #  (as the x and y positions are for the top-left corner)
            x = spawn_pos.x - (SPAWNED_ITEM_HALF_SIZE if should_center[0] else 0)
            y = spawn_pos.y - (SPAWNED_ITEM_HALF_SIZE if should_center[1] else 0)
        else:
            x = random.randint(1100, 1300)
            y = random.randint(self.last_pipe.y - self.pipes.vertical_gap - 50, self.last_pipe.y)

        spawned_item = SpawnedItem(config=self.config, item_name=item_name, x=x, y=y, image=self.config.images.item_spawn_bubble)
        self.spawned_items.append(spawned_item)

    @staticmethod
    def get_random_spawn_item(possible_items: List[ItemName] = None) -> ItemName:
        spawn_chances = get_spawn_chances()

        if possible_items is not None:
            spawn_chances = {item: spawn_chances[item] for item in possible_items if item in spawn_chances}

        total_probability = sum(spawn_chances.values())
        rand = random.uniform(0, total_probability)

        cumulative_prob = 0
        for item_name, probability in spawn_chances.items():
            cumulative_prob += probability
            if rand <= cumulative_prob:
                return item_name

        return ItemName.EMPTY

    def despawn_items(self) -> None:
        items_to_despawn = []
        for item in self.spawned_items:
            if item.x + item.w + 100 < 0:  # check if item is off-screen
                items_to_despawn.append(item)

        for item in items_to_despawn:
            self.spawned_items.remove(item)

    def collect_items(self, items: List[SpawnedItem]) -> None:
        if items:
            for item in items:
                self.config.sounds.play_random(self.config.sounds.collect_item)
                self.spawned_items.remove(item)
                self.inventory.add_item(item.item_name)
