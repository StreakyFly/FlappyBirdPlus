from src.entities.items import Item, ItemType, ItemName


class EmptyItem(Item):
    def __init__(self, *args, **kwargs):
        super().__init__(item_type=ItemType.EMPTY, item_name=ItemName.EMPTY, *args, **kwargs)

    def stop(self):
        pass
