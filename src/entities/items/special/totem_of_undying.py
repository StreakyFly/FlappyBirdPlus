from src.entities.items import Item, ItemType, ItemName


class TotemOfUndying(Item):
    item_type = ItemType.SPECIAL
    item_name = ItemName.TOTEM_OF_UNDYING

    # def __init__(self, *args, **kwargs):
    #     super().__init__(*args, **kwargs)

    def use(self):
        # if self.entity.hpm.current_value <= 0:
        #     self.entity.change_hp(100)
        super().use()
        self.entity.apply_invincibility(duration_frames=100)

        # TODO play an animation & sound

    def stop(self):
        pass
