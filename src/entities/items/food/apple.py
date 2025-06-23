from src.entities.items import ItemName
from .food import Food


class Apple(Food):
    item_name = ItemName.FOOD_APPLE

    def __init__(self, *args, **kwargs):
        super().__init__(
            fill_amount=15,
            *args, **kwargs
        )
