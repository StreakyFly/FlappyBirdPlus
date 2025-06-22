from typing import Dict

from .item_enums import ItemName


def get_spawn_chances() -> Dict[ItemName, float]:
    SPAWN_CHANCES: Dict[ItemName, float] = {
        # WEAPONS
        ItemName.WEAPON_AK47: 0.06,
        ItemName.WEAPON_DEAGLE: 0.04,
        ItemName.WEAPON_UZI: 0.05,

        # AMMUNITION
        ItemName.AMMO_BOX: 0.32,

        # FOOD
        ItemName.FOOD_APPLE: 0.16,
        ItemName.FOOD_BURGER: 0.06,
        ItemName.FOOD_CHOCOLATE: 0.1,

        # POTIONS
        ItemName.POTION_HEAL: 0.1,
        ItemName.POTION_SHIELD: 0.1,

        # HEALS
        ItemName.HEAL_MEDKIT: 0.06,
        ItemName.HEAL_BANDAGE: 0.18,

        # SPECIAL
        ItemName.TOTEM_OF_UNDYING: 0.016,
    }

    return SPAWN_CHANCES
