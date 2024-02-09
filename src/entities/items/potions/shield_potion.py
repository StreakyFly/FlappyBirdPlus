from .potion import Potion


class ShieldPotion(Potion):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def use(self):
        # TODO change so it slowly heals (like slurp potion)
        if self.entity.shield_manager.current_value == self.entity.shield_manager.max_value:
            return
        self.entity.change_shield(75)
        super().use()

