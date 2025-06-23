from src.entities.items import ItemName
from .food import Food


class Burger(Food):
    item_name = ItemName.FOOD_BURGER

    def __init__(self, *args, **kwargs):
        super().__init__(
            fill_amount=60,
            *args, **kwargs
        )
