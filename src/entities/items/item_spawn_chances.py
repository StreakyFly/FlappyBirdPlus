from typing import Dict

from .item_enums import ItemName


def get_spawn_chances() -> Dict[ItemName, float]:
    SPAWN_CHANCES: Dict[ItemName, float] = {
        # WEAPONS
        ItemName.WEAPON_AK47: 0.5,
        ItemName.WEAPON_DEAGLE: 0.5,
        ItemName.WEAPON_UZI: 0.5,

        # AMMUNITION
        ItemName.AMMO_BOX: 0.8,

        # FOOD
        ItemName.FOOD_APPLE: 99,      # TODO: decrease duh x1
        ItemName.FOOD_BURGER: 99,     # TODO: decrease duh x2
        ItemName.FOOD_CHOCOLATE: 99,  # TODO: decrease duh x3

        # POTIONS
        ItemName.POTION_HEAL: 0.8,
        ItemName.POTION_SHIELD: 0.13,

        # HEALS
        ItemName.HEAL_MEDKIT: 0.1,
        ItemName.HEAL_BANDAGE: 0.3,

        # SPECIAL
        ItemName.TOTEM_OF_UNDYING: 0.03,
    }

    return SPAWN_CHANCES
