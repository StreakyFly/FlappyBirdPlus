import math
from typing import Union, List

import pygame

from .entity import Entity
from .items import Item, ItemType, ItemName, ItemInitializer, Gun
from ..utils import GameConfig, flappy_text, get_font, Fonts


class InventorySlot(Entity):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.item: Item = None
        self.type: ItemType = ItemType.EMPTY
        self.font = get_font(Fonts.FONT_FLAPPY, 24)

    def tick(self) -> None:
        self.item.tick()
        super().tick()

    def draw(self) -> None:
        blit_list = [
            (self.config.images.user_interface['inventory-bg-taken' if self.item.name != ItemName.EMPTY else 'inventory-bg-empty'], (self.rect.x + 5, self.rect.y + 5)),
            (self.item.inventory_image if self.item.name != ItemName.EMPTY else self.config.images.items[self.type.value], (self.rect.x + 10, self.rect.y + 10)),
            (self.image, self.rect)]

        if self.item.remaining_cooldown > 0:
            cooldown_overlay, cd_height = self.create_cooldown_overlay()
            blit_list.insert(2, (cooldown_overlay, (self.rect.x + 5, self.rect.y + self.rect.height - cd_height - 10)))

        self.config.screen.blits(blit_list)

        if self.item.name != ItemName.EMPTY:
            text_surface = flappy_text(text=str(self.item.quantity), font=self.font, outline_width=4, outline_algorithm=4)

            text_width, _ = text_surface.get_size()
            text_rect = text_surface.get_rect()
            text_rect.x = self.x - text_width / 1.6 + 92
            text_rect.y = self.y + 66

            self.config.screen.blit(text_surface, text_rect)

    def create_cooldown_overlay(self) -> tuple[pygame.Surface, int]:
        height = int((self.rect.height - 15) * (self.item.remaining_cooldown / self.item.total_cooldown))
        cooldown_overlay = pygame.Surface((self.rect.width - 15, height), pygame.SRCALPHA)
        cooldown_overlay.fill((0, 0, 0, 150))
        return cooldown_overlay, height


class Inventory(Entity):
    def __init__(self, config: GameConfig, player, env) -> None:
        super().__init__(config)
        self.inventory_slots: List[InventorySlot] = []
        self.item_initializer = ItemInitializer(config=config, env=env, entity=player)
        self.create_inventory_slots()
        self.empty_item = self.item_initializer.init_item(ItemName.EMPTY)
        # self.inventory_slots[0].item = self.item_initializer.init_item(ItemName.WEAPON_AK47)
        # self.inventory_slots[0].item.quantity = 1000

    def create_inventory_slots(self) -> None:
        num_slots = 6
        slot_width = (self.config.window.width - 21) / num_slots
        slot_height = self.config.window.viewport_height + 50

        default_item_types = [
            ItemType.EMPTY_WEAPON,
            ItemType.EMPTY_AMMO,
            ItemType.EMPTY_FOOD,
            ItemType.EMPTY_POTION,
            ItemType.EMPTY_HEAL,
            ItemType.EMPTY_SPECIAL
        ]

        for i in range(num_slots):
            x = 24 + i * slot_width
            slot = InventorySlot(self.config, self.config.images.user_interface['inventory-slot'], x=x, y=slot_height)
            slot.item = self.item_initializer.init_item(ItemName.EMPTY)
            slot.type = default_item_types[i]  # set the item type for the slot
            self.inventory_slots.append(slot)

    def tick(self) -> None:
        for slot in self.inventory_slots:
            slot.tick()

    def stop(self) -> None:
        for slot in self.inventory_slots:
            slot.item.stop()

    def add_item(self, item_name: ItemName) -> None:
        for slot in self.inventory_slots:
            if slot.item.name == item_name:
                if slot.item.type == ItemType.WEAPON:
                    self.add_new_item(item_name, slot)
                else:
                    slot.item.quantity += slot.item.spawn_quantity
                return

        if item_name == ItemName.AMMO_BOX:
            # if there's no ammo and no weapon, add one magazine of BULLET_BIG ammo
            if self.inventory_slots[1].item.name == ItemName.EMPTY and self.inventory_slots[0].item.name == ItemName.EMPTY:
                self.add_new_item(ItemName.BULLET_BIG, self.inventory_slots[1])
            # if there's no ammo, but there's a weapon, add one magazine of the corresponding ammo
            # — this shouldn't happen, because you always get ammo with a weapon and even when ammo reaches 0, it remains
            # in the inventory, but just in case, if you programmatically add a weapon, but no ammo (or something like that)
            elif self.inventory_slots[1].item.name == ItemName.EMPTY:
                weapon: Union[Item, Gun] = self.inventory_slots[0].item
                self.add_new_item(weapon.ammo_name, self.inventory_slots[1])
            # if there's ammo, add the corresponding quantity (one weapon magazine) to the existing ammo
            else:
                self.inventory_slots[1].item.quantity += self.inventory_slots[1].item.spawn_quantity
            return

        self.add_new_item(item_name)

    def add_new_item(self, item_name: ItemName, inventory_slot: InventorySlot = None) -> None:
        item_to_add = self.item_initializer.init_item(item_name)

        if item_to_add.type == ItemType.WEAPON:
            current_weapon: Union[Item, Gun] = self.inventory_slots[0].item
            new_weapon: Union[Item, Gun] = item_to_add
            ammo_slot: InventorySlot = self.inventory_slots[1]

            # if this is your first weapon, add corresponding ammo to the ammo inventory slot
            if ammo_slot.item.type == ItemType.EMPTY:
                self.add_new_item(new_weapon.ammo_name, ammo_slot)
            # otherwise, add one magazine of ammo to the existing ammo
            else:
                ammo_slot.item.quantity += ammo_slot.item.spawn_quantity

            # change ammo type and convert the quantity to correspond to the new weapon's magazine size
            if current_weapon.name != new_weapon.name:
                converted_quantity = math.ceil((ammo_slot.item.quantity / ammo_slot.item.spawn_quantity) * new_weapon.magazine_size)
                ammo_slot.item = self.item_initializer.init_item(new_weapon.ammo_name)
                ammo_slot.item.quantity = converted_quantity

            # if there are still spawned bullets, move them to the new weapon, so they don't immediately disappear
            if current_weapon.name != ItemName.EMPTY and current_weapon.shot_bullets:
                new_weapon.shot_bullets = set(current_weapon.shot_bullets)

        if not inventory_slot:
            for slot in self.inventory_slots:
                if slot.type == item_to_add.type or slot.type.value.split('-')[-1] == item_to_add.type.value:
                    inventory_slot = slot
                    break

        inventory_slot.type = item_to_add.type
        inventory_slot.item = item_to_add

    def use_item(self, inventory_slot_index: int) -> None:
        slot = self.inventory_slots[inventory_slot_index]

        if slot.item.type == ItemType.EMPTY:
            return

        if inventory_slot_index in [0, 1]:
            weapon_item: Union[Item, Gun] = self.inventory_slots[0].item
            ammo_item = self.inventory_slots[1].item
            weapon_item.update_ammo_object(ammo_item)  # so the gun can properly reload
            weapon_item.use(inventory_slot_index)
            return

        slot.item.use()
        if slot.item.quantity <= 0:
            slot.item = self.empty_item
            slot.type = ItemType['EMPTY_' + slot.type.value.upper()]
