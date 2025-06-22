from src.entities.items import ItemName
from .potion import Potion


class ShieldPotion(Potion):
    def __init__(self, *args, **kwargs):
        super().__init__(
            item_name=ItemName.POTION_SHIELD,
            fill_amount=75,
            *args, **kwargs
        )

    def use(self):
        # TODO change so it slowly heals (like slurp potion)
        if self.entity.shield_bar.current_value == self.entity.shield_bar.max_value:
            return
        super().use()
        self.entity.shield_bar.change_value_by(self.fill_amount)
