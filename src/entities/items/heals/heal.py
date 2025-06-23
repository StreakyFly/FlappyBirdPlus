from src.entities.items import Item, ItemType


class Heal(Item):
    item_type = ItemType.HEAL

    def __init__(self, fill_amount: int, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fill_amount = fill_amount

    def use(self) -> None:
        if self.entity.hp_bar.current_value == self.entity.hp_bar.max_value:
            return
        super().use()
        self.entity.hp_bar.change_value_by(self.fill_amount)

        # TODO play an animation & sound

    def stop(self):
        pass
