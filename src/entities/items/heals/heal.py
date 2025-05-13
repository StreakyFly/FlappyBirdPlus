from ..item import Item


class Heal(Item):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def use(self, heal_amount: int = 0) -> None:
        if self.entity.hp_manager.current_value == self.entity.hp_manager.max_value:
            return
        super().use()
        self.entity.change_hp(heal_amount)

        # TODO play an animation & sound

    def stop(self):
        pass
