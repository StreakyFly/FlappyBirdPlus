from src.entities.items import Item, ItemType


class Food(Item):
    def __init__(self, *args, **kwargs):
        super().__init__(item_type=ItemType.FOOD, *args, **kwargs)

    def use(self, fill_amount: int = 0) -> None:
        if self.entity.food_bar.current_value == self.entity.food_bar.max_value:
            return
        super().use()
        self.entity.food_bar.change_value_by(fill_amount)

        # TODO play an animation & sound

    def stop(self):
        pass
