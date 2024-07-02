from ..utils import GameConfig
from .entity import Entity


# TODO: Add parallax scrolling to the background
#  so the trees, buildings, and clouds move at slightly different speeds.


class Background(Entity):
    def __init__(self, config: GameConfig) -> None:
        super().__init__(
            config,
            config.images.background,
            0,
            0,
            config.window.width,
            config.window.height,
        )
