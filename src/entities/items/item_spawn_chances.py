from typing import Dict

from .item_enums import ItemName


def get_spawn_chances() -> Dict[ItemName, float]:
    SPAWN_CHANCES: Dict[ItemName, float] = {
        ItemName.TOTEM_OF_UNDYING: 0.03,
        ItemName.MEDKIT: 0.1,
        ItemName.BANDAGE: 0.3,
        ItemName.POTION_HEAL: 0.8,
        ItemName.POTION_SHIELD: 0.13,
        ItemName.WEAPON_AK47: 0.5,
        ItemName.WEAPON_DEAGLE: 0.5,
        ItemName.WEAPON_UZI: 0.5,
        ItemName.AMMO_BOX: 0.8,
    }

    return SPAWN_CHANCES
