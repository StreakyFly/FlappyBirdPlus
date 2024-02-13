import random
import math
from enum import Enum
from typing import List, Tuple, Dict

import pygame

from ...utils import GameConfig
from ..entity import Entity


"""
INVISIBILITY POTION!! MINIGUN THAT OVERHEATS!! Food/hunger...?
"""

# TODO when player collects the item aka. touches the bubble, the bubble should pop (simple animation).


class ItemType(Enum):
    EMPTY = 'empty'
    EMPTY_WEAPON = 'empty-weapon'
    EMPTY_AMMO = 'empty-ammo'
    EMPTY_HEAL = 'empty-heal'
    EMPTY_POTION = 'empty-potion'
    EMPTY_SPECIAL = 'empty-special'

    WEAPON = 'weapon'
    AMMO = 'ammo'
    POTION = 'potion'
    HEAL = 'heal'
    SPECIAL = 'special'


class ItemName(Enum):
    EMPTY = 'empty'

    # SPECIAL
    TOTEM_OF_UNDYING = 'totem-of-undying'

    # HEAL
    MEDKIT = 'medkit'
    BANDAGE = 'bandage'

    # POTION
    POTION_HEAL = 'potion-heal'
    POTION_SHIELD = 'potion-shield'

    # WEAPON
    WEAPON_AK47 = 'ak-47'
    WEAPON_DEAGLE = 'deagle'
    WEAPON_UZI = 'uzi'

    # AMMO
    AMMO_BOX = 'ammo-box'
    BULLET_SMALL = 'small-bullet'
    BULLET_MEDIUM = 'medium-bullet'
    BULLET_BIG = 'big-bullet'


class SpawnedItem(Entity):
    def __init__(self, item_name: ItemName, **kwargs) -> None:
        super().__init__(**kwargs)
        self.item_name = item_name
        self.initial_y = self.y

        self.vel_x = -random.uniform(9, 11)

        random_amplitude = random.uniform(15, 30)
        self.amplitude = random.choice([random_amplitude, -random_amplitude])  # oscillation amplitude
        self.frequency = random.uniform(0.005, 0.009)  # oscillation frequency
        self.sin_y = random.uniform(-self.amplitude, self.amplitude)  # initial vertical position

        if f"{self.item_name.value}_small" in self.config.images.items:
            self.item_image = self.config.images.items[f"{self.item_name.value}_small"]
        else:
            item_img = self.config.images.items[self.item_name.value]
            self.item_image = pygame.transform.scale(item_img, (56, 56))

        self.item_img_x: int = (self.image.get_height() - 56) // 2
        self.item_img_y: int = (self.image.get_width() - 56) // 2

    # def draw(self) -> None:  # old draw, for 'stationary' spawned items (self.vel_x = -7.5)
    #     self.x += self.vel_x
    #     self.config.screen.blit(self.item_image, (self.rect.x + self.item_img_x, self.rect.y + self.item_img_y))
    #     super().draw()

    def draw(self) -> None:
        self.x += self.vel_x
        self.sin_y = self.amplitude * math.sin(self.frequency * self.x)
        self.y = self.initial_y + self.sin_y

        # draw the item image
        item_x = self.rect.x + self.item_img_x
        item_y = self.rect.y + self.item_img_y
        self.config.screen.blit(self.item_image, (item_x, item_y))

        # draw the bubble
        self.config.screen.blit(self.image, (self.rect.x, self.rect.y))

    def stop(self) -> None:
        self.vel_x = 0


class Item(Entity):
    def __init__(
        self,
        config: GameConfig,
        item_type: ItemType,
        item_name: ItemName,
        spawn_quantity: int = 1,
        entity=None,  # in case the Item needs to access attributes of Entity instance, for example its location or HP
        **kwargs
    ) -> None:
        super().__init__(config, **kwargs)
        self.type = item_type
        self.name = item_name
        self.spawn_quantity = spawn_quantity
        self._quantity = spawn_quantity
        self.entity = entity
        if item_name.value + "_inventory" in self.config.images.items:
            self.inventory_image = config.images.items[item_name.value + "_inventory"]
        else:
            self.inventory_image = config.images.items[item_name.value]
        self.update_image(self.config.images.items[self.name.value])
        self.total_cooldown = 0
        self.remaining_cooldown = 0

    @property
    def quantity(self):
        return self._quantity

    @quantity.setter
    def quantity(self, value):
        if value < 0:
            self._quantity = 0
        else:
            self._quantity = value

    def use(self, *args):
        self.quantity -= 1

    def set_cooldown(self, cooldown: int) -> None:
        self.total_cooldown = cooldown
        self.remaining_cooldown = cooldown

    def draw(self) -> None:
        # overrides Entity.draw() as Items should not be drawn on their own, unless it's a weapon or other special item
        # that needs to be drawn on the game canvas, not just in the inventory
        pass


class Items(Entity):
    spawned_items: List[SpawnedItem]
    # TODO set decent spawn chances for each item - maybe even move this to a separate file...?
    spawn_chance: Dict[ItemName, float] = {
        ItemName.TOTEM_OF_UNDYING: 0.03,
        ItemName.MEDKIT: 0.1,
        ItemName.BANDAGE: 0.3,
        ItemName.POTION_HEAL: 0.15,
        ItemName.POTION_SHIELD: 0.13,
        ItemName.WEAPON_AK47: 3,
        ItemName.WEAPON_DEAGLE: 3,
        ItemName.WEAPON_UZI: 5,
        ItemName.AMMO_BOX: 3,
    }

    def __init__(self, config: GameConfig, inventory, pipes, **kwargs):
        super().__init__(config, **kwargs)
        self.config = config
        self.inventory = inventory
        self.pipes = pipes
        self.spawned_items = []

    def tick(self) -> None:
        # self.spawned_items.append(SpawnedItem(config=self.config, item_name=ItemName.POTION_SHIELD,
        #                            x=800, y=700, image=self.config.images.item_spawn_bubble))  # temporary test
        # self.spawned_items.append(SpawnedItem(config=self.config, item_name=ItemName.POTION_HEAL,
        #                            x=800, y=600, image=self.config.images.item_spawn_bubble))  # temporary test
        # self.spawned_items.append(SpawnedItem(config=self.config, item_name=ItemName.TOTEM_OF_UNDYING,
        #                            x=800, y=500, image=self.config.images.item_spawn_bubble))  # temporary test
        # self.spawned_items.append(SpawnedItem(config=self.config, item_name=ItemName.POTION_HEAL,
        #                            x=800, y=400, image=self.config.images.item_spawn_bubble))  # temporary test
        # self.spawned_items.append(SpawnedItem(config=self.config, item_name=ItemName.POTION_SHIELD,
        #                            x=800, y=300, image=self.config.images.item_spawn_bubble))  # temporary test
        # self.spawned_items.append(SpawnedItem(config=self.config, item_name=ItemName.TOTEM_OF_UNDYING,
        #                            x=800, y=200, image=self.config.images.item_spawn_bubble))  # temporary test
        # self.spawned_items.append(SpawnedItem(config=self.config, item_name=ItemName.POTION_SHIELD,
        #                            x=800, y=100, image=self.config.images.item_spawn_bubble))  # temporary test
        # self.spawned_items.append(SpawnedItem(config=self.config, item_name=ItemName.POTION_HEAL,
        #                            x=800, y=0, image=self.config.images.item_spawn_bubble))  # temporary test

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
        total_probability = sum(self.spawn_chance.values())
        rand = random.uniform(0, total_probability)

        cumulative_prob = 0
        for item_name, probability in self.spawn_chance.items():
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
