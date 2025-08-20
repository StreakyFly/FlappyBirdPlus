from typing import Dict

from .item_enums import ItemName


def get_spawn_chances() -> Dict[ItemName, float]:
    SPAWN_CHANCES: Dict[ItemName, float] = {
        # WEAPONS
        ItemName.WEAPON_AK47: 0.03,
        ItemName.WEAPON_DEAGLE: 0.03,
        ItemName.WEAPON_UZI: 0.03,

        # AMMUNITION
        ItemName.AMMO_BOX: 0.30,

        # FOOD
        ItemName.FOOD_APPLE: 0.12,
        ItemName.FOOD_BURGER: 0.05,
        ItemName.FOOD_CHOCOLATE: 0.07,

        # POTIONS
        ItemName.POTION_HEAL: 0.07,
        ItemName.POTION_SHIELD: 0.13,

        # HEALS
        ItemName.HEAL_MEDKIT: 0.06,
        ItemName.HEAL_BANDAGE: 0.16,

        # SPECIAL
        ItemName.TOTEM_OF_UNDYING: 0.016,
    }

    return SPAWN_CHANCES
