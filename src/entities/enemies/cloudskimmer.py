from ...utils import GameConfig, Animation
from .enemy import Enemy

# Medium-sized enemy, doesn't get close but waits on the right side of the screen and uses weapons and other items
# just like player. Attacks in groups of 3.


class CloudSkimmer(Enemy):
    def __init__(self, config: GameConfig, *args, **kwargs):
        super().__init__(config, Animation(config.images.enemies['enemy-temp']), *args, **kwargs)
