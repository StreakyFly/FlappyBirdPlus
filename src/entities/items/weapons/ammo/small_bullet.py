from src.entities.items import ItemName
from .bullet import Bullet


class SmallBullet(Bullet):
    item_name = ItemName.BULLET_SMALL

    # def __init__(self, *args, **kwargs):
    #     super().__init__(*args, **kwargs)
