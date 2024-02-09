from ...utils import GameConfig
from .item import Item, ItemName, ItemType
from .empty_item import EmptyItem
from .special import TotemOfUndying
from .heals import Medkit, Bandage
from .potions import HealPotion, ShieldPotion
from .weapons import AK47, BigBullet


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
                item = EmptyItem(c, t.EMPTY, n.EMPTY, (0, 0))
            case n.TOTEM_OF_UNDYING:
                item = TotemOfUndying(c, t.SPECIAL, n.TOTEM_OF_UNDYING, (1, 1), self.player)
            case n.MEDKIT:
                item = Medkit(c, t.HEAL, n.MEDKIT, (1, 1), self.player)
            case n.BANDAGE:
                item = Bandage(c, t.HEAL, n.BANDAGE, (1, 3), self.player)
            case n.POTION_HEAL:
                item = HealPotion(c, t.POTION, n.POTION_HEAL, (1, 1), self.player)
            case n.POTION_SHIELD:
                item = ShieldPotion(c, t.POTION, n.POTION_SHIELD, (1, 1), self.player)
            case n.WEAPON_AK47:
                item = AK47(config=c, item_type=t.WEAPON, item_name=n.WEAPON_AK47, spawn_quantity_range=(30, 30),
                            entity=self.player, ammo_name=n.BULLET_BIG, ammo_class=BigBullet, damage=35, ammo_speed=25,
                            magazine_size=30, shoot_cooldown=self.config.fps / 3, reload_cooldown=self.config.fps)
            case n.BULLET_BIG:
                item = BigBullet(config=c, item_type=t.AMMO, item_name=n.BULLET_BIG, spawn_quantity_range=(30, 30))
            case _:
                print("Achievement unlocked: How did we get here?")

        return item
