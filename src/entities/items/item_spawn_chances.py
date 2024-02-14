from typing import Dict

from .item_enums import ItemName


def get_spawn_chances() -> Dict[ItemName, float]:
    SPAWN_CHANCES: Dict[ItemName, float] = {
        ItemName.TOTEM_OF_UNDYING: 0.03,
        ItemName.MEDKIT: 0.1,
        ItemName.BANDAGE: 0.3,
        ItemName.POTION_HEAL: 4,
        ItemName.POTION_SHIELD: 0.13,
        ItemName.WEAPON_AK47: 2,
        ItemName.WEAPON_DEAGLE: 2,
        ItemName.WEAPON_UZI: 2,
        ItemName.AMMO_BOX: 3,
    }

    return SPAWN_CHANCES
