from ...utils import GameConfig, Animation
from ..entity import Entity
from ..attribute_bar import AttributeBar


class Enemy(Entity):
    def __init__(self, config: GameConfig, animation: Animation, *args, **kwargs):
        super().__init__(config, *args, **kwargs)
        self.animation: Animation = animation
        self.update_image(self.animation.update())
        self.hp_manager = AttributeBar(config=self.config, max_value=150, color=(255, 0, 0, 222),
                                       x=self.x, y=int(self.y) - 25, w=self.w, h=10)
        self.died = False

    def tick(self):
        self.update_image(self.animation.update())
        self.hp_manager.y = self.y - 25
        self.hp_manager.tick()
        super().tick()

    def change_life(self, amount: int) -> None:
        self.hp_manager.change_value(amount)

        if self.hp_manager.is_empty() and not self.died:
            self.die()

    def die(self) -> None:
        # TODO play death sound
        self.play_death_animation()

    def play_death_animation(self) -> None:
        # TODO implement this

        self.died = True
