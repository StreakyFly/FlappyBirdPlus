from .heal import Heal


class Medkit(Heal):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def use(self, heal_amount=100):
        super().use(heal_amount)
