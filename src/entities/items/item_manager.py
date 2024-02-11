from ...utils import GameConfig
from .item import Item, ItemName, ItemType
from .empty_item import EmptyItem
from .special import TotemOfUndying
from .heals import Medkit, Bandage
from .potions import HealPotion, ShieldPotion
from .weapons import AK47, Deagle, BigBullet


class ItemManager:
    def __init__(self, config: GameConfig, player):
        self.config = config
        self.player = player

    def init_item(self, item_name: ItemName):
        c = self.config
        t = ItemType
        n = ItemName

        item: Item = None
        match item_name:
            case n.EMPTY:
                item = EmptyItem(c, t.EMPTY, n.EMPTY, 0)
            case n.TOTEM_OF_UNDYING:
                item = TotemOfUndying(c, t.SPECIAL, n.TOTEM_OF_UNDYING, 1, self.player)
            case n.MEDKIT:
                item = Medkit(c, t.HEAL, n.MEDKIT, 1, self.player)
            case n.BANDAGE:
                item = Bandage(c, t.HEAL, n.BANDAGE, 3, self.player)
            case n.POTION_HEAL:
                item = HealPotion(c, t.POTION, n.POTION_HEAL, 1, self.player)
            case n.POTION_SHIELD:
                item = ShieldPotion(c, t.POTION, n.POTION_SHIELD, 1, self.player)
            case n.WEAPON_AK47:
                item = AK47(c, t.WEAPON, n.WEAPON_AK47, 30, self.player)
            case n.WEAPON_DEAGLE:
                item = Deagle(c, t.WEAPON, n.WEAPON_DEAGLE, 7, self.player)
            case n.BULLET_BIG:
                item = BigBullet(config=c, item_type=t.AMMO, item_name=n.BULLET_BIG, spawn_quantity=30)
            case _:
                print("Achievement unlocked: How did we get here?")

        return item
