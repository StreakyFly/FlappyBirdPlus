from src.entities.items import ItemName
from .food import Food


class Apple(Food):
    def __init__(self, *args, **kwargs):
        super().__init__(item_name=ItemName.FOOD_APPLE, *args, **kwargs)

    def use(self, fill_amount=15):
        super().use(fill_amount)
