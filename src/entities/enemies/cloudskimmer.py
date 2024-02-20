import random
import math

from ...utils import GameConfig, Animation
from .enemy import Enemy, EnemyGroup

# Medium-sized enemy, doesn't get close but waits on the right side of the screen and uses weapons and other items
# just like player. Attacks in groups of 3.
# One in front center, the other two are slightly behind, one below and one above.


class CloudSkimmer(Enemy):
    def __init__(self, config: GameConfig, *args, **kwargs):
        super().__init__(config, Animation(config.images.enemies['enemy-temp']), *args, **kwargs)

        self.initial_y = self.y
        self.vel_x = -9
        # random_amplitude = random.uniform(15, 30)
        # self.amplitude = random.choice([random_amplitude, -random_amplitude])  # oscillation amplitude
        # self.sin_y = random.uniform(-self.amplitude, self.amplitude)  # initial relative vertical position
        self.amplitude = 15  # oscillation amplitude
        self.frequency = 0.017  # oscillation frequency
        self.sin_y = 0  # initial relative vertical position

    def tick(self):
        self.x += self.vel_x
        self.sin_y = self.amplitude * math.sin(self.frequency * self.x)
        self.y = self.initial_y + self.sin_y
        super().tick()


class CloudSkimmerGroup(EnemyGroup):
    def __init__(self, config: GameConfig, x: int, y: int, *args, **kwargs):
        super().__init__(config, x, y, *args, **kwargs)
        self.members = [CloudSkimmer(self.config, x=self.x, y=self.y + i * 100) for i in range(3)]
