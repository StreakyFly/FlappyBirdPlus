from src.entities.items import Item, ItemType, ItemName


class EmptyItem(Item):
    item_type = ItemType.EMPTY
    item_name = ItemName.EMPTY

    # def __init__(self, *args, **kwargs):
    #     super().__init__(*args, **kwargs)

    def stop(self):
        pass
