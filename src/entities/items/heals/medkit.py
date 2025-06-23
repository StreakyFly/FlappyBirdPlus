from src.entities.items import ItemName
from .heal import Heal


class Medkit(Heal):
    item_name = ItemName.HEAL_MEDKIT

    def __init__(self, *args, **kwargs):
        super().__init__(
            fill_amount=100,
            *args, **kwargs
        )
