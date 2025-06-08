from src.entities.items import ItemName
from .potion import Potion


class HealPotion(Potion):
    def __init__(self, *args, **kwargs):
        super().__init__(item_name=ItemName.POTION_HEAL, *args, **kwargs)

    def use(self):
        # TODO change so it slowly heals (like slurp potion)
        if self.entity.hp_bar.current_value == self.entity.hp_bar.max_value:
            return
        super().use()
        self.entity.hp_bar.change_value_by(75)
