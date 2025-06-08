from src.entities.items import Item, ItemType, ItemName


class TotemOfUndying(Item):
    def __init__(self, *args, **kwargs):
        super().__init__(item_type=ItemType.SPECIAL, item_name=ItemName.TOTEM_OF_UNDYING, *args, **kwargs)

    # @property
    # def quantity(self):
    #     return self._quantity
    #
    # @quantity.setter
    # def quantity(self, value):
    #     if value <= 0:
    #         self._quantity = 0
    #     else:
    #         self._quantity = 1

    def use(self):
        # if self.entity.hpm.current_value <= 0:
        #     self.entity.change_hp(100)
        super().use()
        self.entity.apply_invincibility(duration_frames=60)

        # TODO play an animation & sound

    def stop(self):
        pass
