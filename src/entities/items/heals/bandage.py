from src.entities.items import ItemName
from .heal import Heal


class Bandage(Heal):
    def __init__(self, *args, **kwargs):
        super().__init__(
            item_name=ItemName.HEAL_BANDAGE,
            fill_amount=15,
            *args, **kwargs
        )
