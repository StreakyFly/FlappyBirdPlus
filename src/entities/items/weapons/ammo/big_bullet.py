from .bullet import Bullet


class BigBullet(Bullet):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # super().__init__(spawn_pos_offset=lambda x: pygame.Vector2(self.w / 2, 0), *args, **kwargs)
