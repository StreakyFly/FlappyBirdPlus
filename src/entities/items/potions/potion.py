from src.entities.items import Item, ItemType


class Potion(Item):
    def __init__(self, fill_amount: int, *args, **kwargs):
        super().__init__(item_type=ItemType.POTION, *args, **kwargs)
        self.fill_amount = fill_amount

    def use(self):
        super().use()
        # TODO do something like play an animation & sound and do whatever the potion does

    def stop(self):
        pass
