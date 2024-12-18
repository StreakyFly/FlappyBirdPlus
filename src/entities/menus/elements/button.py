from src.utils import GameConfig
from src.entities.entity import Entity


class Button(Entity):
    def __init__(self, config: GameConfig, image, x, y):
        image = image or config.images.user_interface['button-wide']
        super().__init__(
            config=config,
            image=image,
            x=x,
            y=y,
        )

    def tick(self):
        super().tick()

    def draw(self):
        super().draw()
