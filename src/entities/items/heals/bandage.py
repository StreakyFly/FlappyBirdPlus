from .heal import Heal


class Bandage(Heal):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def use(self, heal_amount=15):
        super().use(heal_amount)
