import random

from src.utils import GameConfig, printc
from .empty_item import EmptyItem
from .food import Apple, Burger, Chocolate
from .heals import Medkit, Bandage
from .item import Item
from .item_enums import ItemName
from .potions import HealPotion, ShieldPotion
from .special import TotemOfUndying
from .weapons import AK47, Deagle, Uzi, AmmoBox, BigBullet, MediumBullet, SmallBullet

ITEM_NAME_TO_CLASS_MAP = {
    ItemName.EMPTY: EmptyItem,

    # Weapons
    ItemName.WEAPON_AK47: AK47,
    ItemName.WEAPON_DEAGLE: Deagle,
    ItemName.WEAPON_UZI: Uzi,

    # Ammunition
    ItemName.AMMO_BOX: AmmoBox,
    ItemName.BULLET_BIG: BigBullet,
    ItemName.BULLET_MEDIUM: MediumBullet,
    ItemName.BULLET_SMALL: SmallBullet,

    # Food
    ItemName.FOOD_APPLE: Apple,
    ItemName.FOOD_BURGER: Burger,
    ItemName.FOOD_CHOCOLATE: Chocolate,

    # Potions
    ItemName.POTION_HEAL: HealPotion,
    ItemName.POTION_SHIELD: ShieldPotion,

    # Heals
    ItemName.HEAL_MEDKIT: Medkit,
    ItemName.HEAL_BANDAGE: Bandage,

    # Special
    ItemName.TOTEM_OF_UNDYING: TotemOfUndying,
}


class ItemInitializer:
    def __init__(self, config: GameConfig, env=None, entity=None):
        self.config = config
        self.env = env
        self.entity = entity

    def init_item(self, item_name: ItemName, entity=None) -> Item:
        entity = entity or self.entity
        c = self.config
        n = ItemName

        item: Item = None  # type: ignore
        match item_name:  # noqa
            case n.EMPTY:
                item = EmptyItem(config=c, spawn_quantity=0)

            # Weapons
            case n.WEAPON_AK47:
                item = AK47(config=c, spawn_quantity=30, entity=entity, env=self.env)
            case n.WEAPON_DEAGLE:
                item = Deagle(config=c, spawn_quantity=7, entity=entity, env=self.env)
            case n.WEAPON_UZI:
                item = Uzi(config=c, spawn_quantity=32, entity=entity, env=self.env)

            # Ammunition
            case n.AMMO_BOX:
                item = AmmoBox(config=c, spawn_quantity=30)
            case n.BULLET_BIG:
                item = BigBullet(config=c, spawn_quantity=30)
            case n.BULLET_MEDIUM:
                item = MediumBullet(config=c, spawn_quantity=7)
            case n.BULLET_SMALL:
                item = SmallBullet(config=c, spawn_quantity=32)

            # Food
            case n.FOOD_APPLE:
                item = Apple(config=c, spawn_quantity=random.randint(2, 4), entity=entity)
            case n.FOOD_BURGER:
                item = Burger(config=c, spawn_quantity=1, entity=entity)
            case n.FOOD_CHOCOLATE:
                item = Chocolate(config=c, spawn_quantity=random.randint(1, 2), entity=entity)

            # Potions
            case n.POTION_HEAL:
                item = HealPotion(config=c, spawn_quantity=random.randint(1, 2), entity=entity)
            case n.POTION_SHIELD:
                item = ShieldPotion(config=c, spawn_quantity=random.randint(1, 2), entity=entity)

            # Heals
            case n.HEAL_MEDKIT:
                item = Medkit(config=c, spawn_quantity=1, entity=entity)
            case n.HEAL_BANDAGE:
                item = Bandage(config=c, spawn_quantity=random.randint(2, 4), entity=entity)

            # Special
            case n.TOTEM_OF_UNDYING:
                item = TotemOfUndying(config=c, spawn_quantity=1, entity=entity)

            case _:
                printc("Achievement unlocked: How did we get here?", color="red")

        return item
