import random
from typing import List

from ...utils import GameConfig
from .item_enums import ItemName
from .item_spawn_chances import get_spawn_chances
from .item import SpawnedItem


class ItemManager:
    def __init__(self, config: GameConfig, inventory, pipes):
        self.config = config
        self.inventory = inventory
        self.pipes = pipes
        self.spawned_items: List[SpawnedItem] = []

    def tick(self) -> None:
        # self.spawned_items.append(SpawnedItem(config=self.config, item_name=ItemName.POTION_SHIELD,
        #                            x=800, y=700, image=self.config.images.item_spawn_bubble))
        # self.spawned_items.append(SpawnedItem(config=self.config, item_name=ItemName.POTION_HEAL,
        #                            x=800, y=600, image=self.config.images.item_spawn_bubble))
        # self.spawned_items.append(SpawnedItem(config=self.config, item_name=ItemName.TOTEM_OF_UNDYING,
        #                            x=800, y=500, image=self.config.images.item_spawn_bubble))
        # self.spawned_items.append(SpawnedItem(config=self.config, item_name=ItemName.POTION_HEAL,
        #                            x=800, y=400, image=self.config.images.item_spawn_bubble))
        # self.spawned_items.append(SpawnedItem(config=self.config, item_name=ItemName.POTION_SHIELD,
        #                            x=800, y=300, image=self.config.images.item_spawn_bubble))
        # self.spawned_items.append(SpawnedItem(config=self.config, item_name=ItemName.TOTEM_OF_UNDYING,
        #                            x=800, y=200, image=self.config.images.item_spawn_bubble))
        # self.spawned_items.append(SpawnedItem(config=self.config, item_name=ItemName.POTION_SHIELD,
        #                            x=800, y=100, image=self.config.images.item_spawn_bubble))
        # self.spawned_items.append(SpawnedItem(config=self.config, item_name=ItemName.POTION_HEAL,
        #                            x=800, y=0, image=self.config.images.item_spawn_bubble))

        if self.can_spawn_item():
            self.spawn_item()

        for item in self.spawned_items:
            item.tick()
        self.despawn_items()

    def stop(self) -> None:
        for item in self.spawned_items:
            item.stop()

    def can_spawn_item(self) -> bool:
        self.last_pipe = self.pipes.lower[-1]
        # return True

        if self.config.window.width - (self.last_pipe.x + self.last_pipe.w) > self.last_pipe.w * 1.9:
            return random.random() <= 1.4  # 0.4  # 40% chance of returning True to spawn an item
        return False

    def spawn_item(self) -> None:
        item_name: ItemName = self.get_random_spawn_item()
        x = random.randint(800, 1200)
        # TODO improve this placement (if you uncomment return True in can_spawn_item() the spawned stream
        #  should run through the gaps, and not lag behind like it does now...) - maybe calculate spawn location
        #  by coming up with a good position at X where the bird is in the screen, and then reverse calculate the
        #  position where it should be spawned (include the amplitude and frequency of the spawned item)
        y = random.randint(self.last_pipe.y - self.pipes.pipe_gap - 50, self.last_pipe.y)

        spawned_item = SpawnedItem(config=self.config, item_name=item_name,
                                   x=x, y=y, image=self.config.images.item_spawn_bubble)
        self.spawned_items.append(spawned_item)

    def get_random_spawn_item(self) -> ItemName:
        total_probability = sum(get_spawn_chances().values())
        rand = random.uniform(0, total_probability)

        cumulative_prob = 0
        for item_name, probability in get_spawn_chances().items():
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
