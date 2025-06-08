from src.entities.items import ItemName
from .bullet import Bullet


class BigBullet(Bullet):
    def __init__(self, *args, **kwargs):
        super().__init__(item_name=ItemName.BULLET_BIG, *args, **kwargs)
        # super().__init__(spawn_pos_offset=lambda x: pygame.Vector2(self.w / 2, 0), *args, **kwargs)
