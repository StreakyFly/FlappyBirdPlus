from src.utils import GameConfig, printc
from .item import Item
from .item_enums import ItemName, ItemType
from .empty_item import EmptyItem
from .special import TotemOfUndying
from .heals import Medkit, Bandage
from .potions import HealPotion, ShieldPotion
from .weapons import AK47, Deagle, Uzi, AmmoBox, BigBullet, MediumBullet, SmallBullet


class ItemInitializer:
    def __init__(self, config: GameConfig, env=None, entity=None):
        self.config = config
        self.env = env
        self.entity = entity

    def init_item(self, item_name: ItemName, entity=None) -> Item:
        entity = entity if entity else self.entity
        c = self.config
        t = ItemType
        n = ItemName

        item: Item = None
        match item_name:
            case n.EMPTY:
                item = EmptyItem(c, t.EMPTY, n.EMPTY, 0)
            case n.TOTEM_OF_UNDYING:
                item = TotemOfUndying(c, t.SPECIAL, n.TOTEM_OF_UNDYING, 1, entity)
            case n.MEDKIT:
                item = Medkit(c, t.HEAL, n.MEDKIT, 1, entity)
            case n.BANDAGE:
                item = Bandage(c, t.HEAL, n.BANDAGE, 3, entity)
            case n.POTION_HEAL:
                item = HealPotion(c, t.POTION, n.POTION_HEAL, 1, entity)
            case n.POTION_SHIELD:
                item = ShieldPotion(c, t.POTION, n.POTION_SHIELD, 1, entity)
            case n.WEAPON_AK47:
                item = AK47(config=c, item_type=t.WEAPON, item_name=n.WEAPON_AK47, spawn_quantity=30, entity=entity, env=self.env)
            case n.WEAPON_DEAGLE:
                item = Deagle(config=c, item_type=t.WEAPON, item_name=n.WEAPON_DEAGLE, spawn_quantity=7, entity=entity, env=self.env)
            case n.WEAPON_UZI:
                item = Uzi(config=c, item_type=t.WEAPON, item_name=n.WEAPON_UZI, spawn_quantity=32, entity=entity, env=self.env)
            case n.AMMO_BOX:
                item = AmmoBox(config=c, item_type=t.AMMO, item_name=n.AMMO_BOX, spawn_quantity=30)
            case n.BULLET_BIG:
                item = BigBullet(config=c, item_type=t.AMMO, item_name=n.BULLET_BIG, spawn_quantity=30)
            case n.BULLET_MEDIUM:
                item = MediumBullet(config=c, item_type=t.AMMO, item_name=n.BULLET_MEDIUM, spawn_quantity=7)
            case n.BULLET_SMALL:
                item = SmallBullet(config=c, item_type=t.AMMO, item_name=n.BULLET_SMALL, spawn_quantity=32)
            case _:
                printc("Achievement unlocked: How did we get here?", color="red")

        return item
