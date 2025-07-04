import math
import random

import pygame

from src.entities.entity import Entity
from src.utils import GameConfig
from .item_enums import ItemName, ItemType


class SpawnedItem(Entity):
    def __init__(self, item_name: ItemName, **kwargs) -> None:
        super().__init__(**kwargs)
        self.item_name = item_name
        self.initial_y = self.y

        self.vel_x = -random.uniform(9, 11)

        random_amplitude = random.uniform(15, 30)
        self.amplitude = random.choice([random_amplitude, -random_amplitude])  # oscillation amplitude
        self.frequency = random.uniform(0.005, 0.009)  # oscillation frequency
        self.sin_y = random.uniform(-self.amplitude, self.amplitude)  # initial relative vertical position

        if f"{self.item_name.value}_small" in self.config.images.items:
            self.item_image = self.config.images.items[f"{self.item_name.value}_small"]
        else:
            item_img = self.config.images.items[self.item_name.value]
            self.item_image = pygame.transform.scale(item_img, (56, 56))

        self.item_img_x: int = (self.h - 56) // 2
        self.item_img_y: int = (self.w - 56) // 2

    def tick(self) -> None:
        self.x += self.vel_x
        self.sin_y = self.amplitude * math.sin(self.frequency * self.x)
        self.y = self.initial_y + self.sin_y
        super().tick()

    def draw(self) -> None:
        # draw the item image
        item_x = self.rect.x + self.item_img_x
        item_y = self.rect.y + self.item_img_y
        self.config.screen.blit(self.item_image, (item_x, item_y))

        # draw the bubble
        self.config.screen.blit(self.image, self.rect)

    def stop(self) -> None:
        self.vel_x = 0


class Item(Entity):
    item_type: ItemType = None
    item_name: ItemName = None

    def __init__(
        self,
        config: GameConfig,
        spawn_quantity: int = 1,
        entity=None,  # in case the Item needs to access attributes/methods of Entity instance, for example its HP
        flipped: bool = False,  # flips the image horizontally, so enemies can use items too
        **kwargs
    ) -> None:
        super().__init__(config, **kwargs)

        item_type = self.__class__.item_type
        item_name = self.__class__.item_name
        if item_type is None or item_name is None:
            raise NotImplementedError("Item subclass must define item_type and item_name class attributes")

        self.spawn_quantity = spawn_quantity
        self._quantity = spawn_quantity
        self.entity = entity
        self.flipped = flipped
        self.total_cooldown = 0
        self.remaining_cooldown = 0  # needs to be handled in the subclass

        item_name_suffix = "_inventory" if f"{item_name.value}_inventory" in self.config.images.items else ""
        self.inventory_image = config.images.items[f"{item_name.value}{item_name_suffix}"]

        if item_type == ItemType.WEAPON:
            self.update_image(self.config.images.items[item_name.value])
        else:
            self.image = self.config.images.items[item_name.value]

    @property
    def quantity(self):
        return self._quantity

    @quantity.setter
    def quantity(self, value):
        self._quantity = max(0, value)

    def tick(self) -> None:
        if self.remaining_cooldown > 0:
            self.remaining_cooldown -= 1
        super().tick()

    def use(self, *args):
        self.quantity -= 1

    def set_cooldown(self, cooldown: int) -> None:
        self.total_cooldown = cooldown
        self.remaining_cooldown = cooldown + 1  # +1, because item is ticked before the InventorySlot is drawn

    def draw(self) -> None:
        # Overrides Entity.draw() as Items should not be drawn on their own, unless it's a weapon or other
        # special item that needs to be drawn in the game world, not just in the inventory.
        pass

    def flip(self) -> None:
        self.flipped = not self.flipped
        self.image = pygame.transform.flip(self.image, True, False)

    def stop(self) -> None:
        raise NotImplementedError("stop() method must be implemented in the subclass")
