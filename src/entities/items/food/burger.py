from src.entities.items import ItemName
from .food import Food


class Burger(Food):
    def __init__(self, *args, **kwargs):
        super().__init__(item_name=ItemName.FOOD_BURGER, *args, **kwargs)

    def use(self, fill_amount=60):
        super().use(fill_amount)
