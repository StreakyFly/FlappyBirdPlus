from src.entities.items import ItemName
from .bullet import Bullet


class MediumBullet(Bullet):
    def __init__(self, *args, **kwargs):
        super().__init__(item_name=ItemName.BULLET_MEDIUM, *args, **kwargs)
