from .potion import Potion


class HealPotion(Potion):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def use(self):
        # TODO change so it slowly heals (like slurp potion)
        if self.entity.hp_manager.current_value == self.entity.hp_manager.max_value:
            return
        self.entity.change_hp(75)
        super().use()
