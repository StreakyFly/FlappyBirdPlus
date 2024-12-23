from src.utils import GameConfig
from src.entities.entity import Entity
from .menu_manager import MenuManager


class Menu(Entity):
    SIDE_PADDING = 40

    def __init__(self, config: GameConfig, menu_manager: MenuManager):
        image = config.images.user_interface['menu']
        super().__init__(
            config=config,
            image=image,
            x=(config.window.width - image.get_width()) // 2,
            y=(config.window.height - image.get_height()) // 2,
        )
        self.menu_manager = menu_manager
        self.elements: list = []

    def tick(self):
        super().tick()
        for element in self.elements:
            element.tick()

    def draw(self):
        super().draw()

    def add_element(self, element, x, y, align="center"):
        match align:
            case "center":
                element.x = x + self.x + (self.w // 2 - element.w // 2)
            case "left":
                element.x = x + self.x + self.SIDE_PADDING
            case "right":
                element.x = x + self.x + self.w - element.w - self.SIDE_PADDING
            case _:
                raise ValueError(f"Invalid alignment: {align}")

        element.y = y + self.y

        # If the element has an init method, call it, as it may need to set up some things based on its new position
        if hasattr(element, "init"):
            element.init()
        self.elements.append(element)

    def handle_event(self, event):
        for element in self.elements:
            element.handle_event(event)
