from src.entities.items import ItemName
from .food import Food


class Chocolate(Food):
    def __init__(self, *args, **kwargs):
        super().__init__(item_name=ItemName.FOOD_CHOCOLATE, *args, **kwargs)

    def use(self, fill_amount=25):
        super().use(fill_amount)
