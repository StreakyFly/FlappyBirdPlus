from .item import Item


class EmptyItem(Item):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def stop(self):
        pass
