from src.entities.items import ItemName
from .food import Food


class Chocolate(Food):
    item_name = ItemName.FOOD_CHOCOLATE

    def __init__(self, *args, **kwargs):
        super().__init__(
            fill_amount=25,
            *args, **kwargs
        )
