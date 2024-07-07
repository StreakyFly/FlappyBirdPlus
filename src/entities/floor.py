from ..utils import GameConfig
from .entity import Entity


class Floor(Entity):
    def __init__(self, config: GameConfig) -> None:
        super().__init__(config, config.images.floor, 0, config.window.viewport_height)
        self.vel_x = 7.5
        self.x_extra = self.w - config.window.width

    def stop(self) -> None:
        self.vel_x = 0

    def tick(self) -> None:
        self.x = -((-self.x + self.vel_x) % self.x_extra)
        super().tick()
