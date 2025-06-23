from src.entities.items import ItemName
from .bullet import Bullet


class MediumBullet(Bullet):
    item_name = ItemName.BULLET_MEDIUM

    # def __init__(self, *args, **kwargs):
    #     super().__init__(*args, **kwargs)
