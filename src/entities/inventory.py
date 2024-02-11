import math
from typing import List, Union

from ..utils import GameConfig, flappy_text, load_font, Fonts
from .entity import Entity
from .items import Item, ItemType, ItemName, ItemManager, Gun


class InventorySlot(Entity):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.item: Item = None
        self.type: ItemType = ItemType.EMPTY
        # self.item_quantity = 0
        self.font = load_font(Fonts.FONT_FLAPPY, 24)

    def draw(self) -> None:
        blit_list = [
            (self.config.images.inventory_backgrounds[self.type.value], (self.rect.x + 5, self.rect.y + 5)),
            (self.item.inventory_image, (self.rect.x + 10, self.rect.y + 10)),
            (self.image, self.rect)]

        self.config.screen.blits(blit_list)

        if self.item.quantity != 0 or self.item.type in [ItemType.WEAPON, ItemType.AMMO]:
            text_surface = flappy_text(text=str(self.item.quantity), font=self.font, outline_width=4,
                                       outline_algorithm=4)

            text_rect = text_surface.get_rect()
            text_rect.y, text_rect.x = self.y + 63, self.x + 74

            self.config.screen.blit(text_surface, text_rect)

    def cooldown(self) -> None:
        # inventory slot cooldown, basically just a partly transparent rectangle covering the slot
        # and slowly moving down with timer in the middle of the slot like in many other games
        # Will be used when reloading a gun and after using certain items
        pass


class Inventory(Entity):
    inventory_slots: List[InventorySlot]
    empty_item: Item = None

    def __init__(self, config: GameConfig, player) -> None:
        super().__init__(config)
        self.inventory_slots = []
        self.item_manager = ItemManager(config, player)
        self.create_inventory_slots()
        self.empty_item = self.item_manager.init_item(ItemName.EMPTY)

    def create_inventory_slots(self) -> None:
        num_slots = 6
        slot_width = (self.config.window.width - 21) / num_slots
        slot_height = self.config.window.viewport_height + 50

        default_item_types = [
            ItemType.EMPTY_WEAPON,
            ItemType.EMPTY_AMMO,
            ItemType.EMPTY,  # TODO -> FOOD...? Or grenades, bombs? Or maybe something else.
            ItemType.EMPTY_POTION,
            ItemType.EMPTY_HEAL,
            ItemType.EMPTY_SPECIAL
        ]

        for i in range(num_slots):
            x = 24 + i * slot_width
            slot = InventorySlot(self.config, self.config.images.inventory_slot, x=x, y=slot_height)
            slot.item = self.item_manager.init_item(ItemName.EMPTY)
            slot.type = default_item_types[i]  # set the item type for the slot
            self.inventory_slots.append(slot)

    def tick(self) -> None:
        for slot in self.inventory_slots:
            slot.tick()
            if slot.item.type == ItemType.WEAPON:
                slot.item.tick()  # TODO you might want to improve this, as right now this is only used for gun cooldown
                                  #  and no other items - maybe you'd like to use this with potions as well, so they slowly heal?

    def add_item(self, item_name: ItemName) -> None:
        for slot in self.inventory_slots:
            if slot.item.name == item_name:
                if slot.item.type == ItemType.WEAPON:
                    weapon: Union[Item, Gun] = slot.item
                    slot.item.quantity = weapon.magazine_size
                    self.inventory_slots[1].item.quantity += weapon.magazine_size  # add one additional ammo magazine
                else:
                    slot.item.quantity += slot.item.spawn_quantity
                return

        if item_name == ItemName.AMMO_BOX:
            # if there's no ammo and no weapon, add one magazine of BULLET_BIG ammo
            if self.inventory_slots[1].item.name == ItemName.EMPTY and self.inventory_slots[0].item.name == ItemName.EMPTY:
                self.add_new_item(ItemName.BULLET_BIG, self.inventory_slots[1])
            # if there's ammo, add the corresponding quantity (one weapon magazine) to the existing ammo
            else:
                self.inventory_slots[1].item.quantity += self.inventory_slots[1].item.spawn_quantity
            return

        self.add_new_item(item_name)

    def add_new_item(self, item_name: ItemName, inventory_slot: InventorySlot = None):
        item_to_add = self.item_manager.init_item(item_name)

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
                converted_quantity = math.ceil((ammo_slot.item.quantity / ammo_slot.item.spawn_quantity) * item_to_add.magazine_size)
                ammo_slot.item = self.item_manager.init_item(new_weapon.ammo_name)
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
            # self.use_weapon(inventory_slot_index)
            weapon_slot = self.inventory_slots[0]
            ammo_slot = self.inventory_slots[1]
            # TODO gun.use() could return either -1 if it's not reloading, or self.reloading_cooldown: int, so we can
            #  then call InventorySlot's cooldown() method for visual effects
            weapon_slot.item.use(inventory_slot_index, ammo_slot.item)  # ammo: Item, so the gun can properly reload
            return

        slot.item.use()
        if slot.item.quantity <= 0:
            slot.item = self.empty_item
            slot.type = ItemType['EMPTY_' + slot.type.value.upper()]
