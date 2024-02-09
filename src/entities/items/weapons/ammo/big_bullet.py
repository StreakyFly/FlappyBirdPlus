from .ammo import Ammo


class BigBullet(Ammo):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
