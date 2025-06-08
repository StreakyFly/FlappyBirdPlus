from src.entities.items import Item, ItemType, ItemName


class AmmoBox(Item):
    def __init__(self, *args, **kwargs):
        super().__init__(item_type=ItemType.AMMO, item_name=ItemName.AMMO_BOX, *args, **kwargs)
