from .bullet import Bullet


class MediumBullet(Bullet):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
