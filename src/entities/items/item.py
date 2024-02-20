import random
import math

import pygame

from ...utils import GameConfig
from ..entity import Entity
from .item_enums import ItemName, ItemType


"""
INVISIBILITY POTION!! MINIGUN THAT OVERHEATS!! Food/hunger...?
"""

# TODO when player collects the item aka. touches the bubble, the bubble should pop (simple animation).


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
        entity=None,  # in case the Item needs to access attributes/methods of Entity instance, for example its HP
        **kwargs
    ) -> None:
        super().__init__(config, **kwargs)
        self.type = item_type
        self.name = item_name
        self.spawn_quantity = spawn_quantity
        self._quantity = spawn_quantity
        self.entity = entity
        item_name_suffix = "_inventory" if item_name.value + "_inventory" in self.config.images.items else ""
        self.inventory_image = config.images.items[item_name.value + item_name_suffix]
        if self.type == ItemType.WEAPON:
            self.update_image(self.config.images.items[self.name.value])
        else:
            self.image = self.config.images.items[self.name.value]
        self.image = self.config.images.items[self.name.value]
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
