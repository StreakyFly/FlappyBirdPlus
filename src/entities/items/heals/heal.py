from src.entities.items import Item, ItemType


class Heal(Item):
    def __init__(self, *args, **kwargs):
        super().__init__(item_type=ItemType.HEAL, *args, **kwargs)

    def use(self, heal_amount: int = 0) -> None:
        if self.entity.hp_bar.current_value == self.entity.hp_bar.max_value:
            return
        super().use()
        self.entity.hp_bar.change_value_by(heal_amount)

        # TODO play an animation & sound

    def stop(self):
        pass
