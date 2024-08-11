from enum import Enum

"""
Other item type ideas:
 - food (bird flaps less high when hungry, starts loosing health when starving)
 - armor (reduces damage taken/bounces back some projectiles)
 - actual shield in front of the bird (bounces back projectiles)
 - magical scrolls (teleport forward (invincible for 3 seconds after teleport),
    freeze time, make pipes temporarily move further apart vertically or even together, to squish entities)
 - tiny robot that helps you (shoots at enemies, maybe even shields you and collects items)
"""


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

    # WEAPONS
    WEAPON_AK47 = 'ak-47'
    WEAPON_DEAGLE = 'deagle'
    WEAPON_UZI = 'uzi'

    # AMMUNITION
    AMMO_BOX = 'ammo-box'
    BULLET_SMALL = 'small-bullet'
    BULLET_MEDIUM = 'medium-bullet'
    BULLET_BIG = 'big-bullet'

    # TBD slot 3

    # POTIONS
    POTION_HEAL = 'potion-heal'
    POTION_SHIELD = 'potion-shield'

    # HEALS
    MEDKIT = 'medkit'
    BANDAGE = 'bandage'

    # SPECIAL
    TOTEM_OF_UNDYING = 'totem-of-undying'
