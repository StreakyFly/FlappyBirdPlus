from src.utils import GameConfig
from src.entities.entity import Entity


# TODO: uhh idk, this will be a menu base that can be reused

# TODO: to keep things simple, use one menu image and then draw elements on top,
#  like menu title and other things


class Menu(Entity):
    def __init__(self, config: GameConfig):
        image = config.images.user_interface['menu']
        super().__init__(
            config=config,
            image=image,
            x=(config.window.width - image.get_width()) // 2,
            y=(config.window.height - image.get_height()) // 2,
        )

    def tick(self):
        super().tick()

    def draw(self):
        super().draw()
