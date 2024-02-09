from ..item import Item


class Potion(Item):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def use(self):
        super().use()
        # TODO do something like play an animation & sound and do whatever the potion does
