from src.entities.items import ItemName
from .heal import Heal


class Bandage(Heal):
    item_name = ItemName.HEAL_BANDAGE

    def __init__(self, *args, **kwargs):
        super().__init__(
            fill_amount=15,
            *args, **kwargs
        )
