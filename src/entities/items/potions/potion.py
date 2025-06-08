from src.entities.items import Item, ItemType


class Potion(Item):
    def __init__(self, *args, **kwargs):
        super().__init__(item_type=ItemType.POTION, *args, **kwargs)

    def use(self):
        super().use()
        # TODO do something like play an animation & sound and do whatever the potion does

    def stop(self):
        pass
