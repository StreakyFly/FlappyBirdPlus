from src.entities.items import ItemName
from .heal import Heal


class Medkit(Heal):
    def __init__(self, *args, **kwargs):
        super().__init__(
            item_name=ItemName.HEAL_MEDKIT,
            fill_amount=100,
            *args, **kwargs
        )
