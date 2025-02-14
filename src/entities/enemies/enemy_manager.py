import random

from src.utils import GameConfig
from .enemy import EnemyGroup
from .cloudskimmer import CloudSkimmerGroup
from .skydart import SkyDartGroup


class EnemyManager:
    def __init__(self, config: GameConfig, env):
        self.config = config
        self.env = env
        self.spawned_enemy_groups = []  # some files expect this list to contain no more than one enemy group at once
        self.count = 0
        self.wait = 240
        self.group_to_spawn = self.spawn_skydart

    def tick(self):
        if self.can_spawn_enemy():
            self.spawn_enemy()

        for group in self.spawned_enemy_groups:
            if group.is_empty():
                self.spawned_enemy_groups.remove(group)
            group.tick()

    def stop(self):
        for group in self.spawned_enemy_groups:
            group.stop()

    def can_spawn_enemy(self) -> bool:
        # TODO improve spawning logic
        if self.spawned_enemy_groups:
            return False
        self.count += 1
        if self.count < self.wait:
            return False
        self.wait = random.randint(120, 300)
        self.count = 0
        return True

    def spawn_enemy(self) -> None:
        # TODO implement this
        # self.spawn_cloudskimmer()  # temporary
        # self.spawn_skydart()  # temporary
        self.group_to_spawn()
        self.group_to_spawn = self.spawn_skydart if self.group_to_spawn == self.spawn_cloudskimmer else self.spawn_cloudskimmer

    def spawn_cloudskimmer(self):
        # TODO play sound effect when spawning enemy, for this one some ghost sound effect

        # Warning! Changing the x and y position will require additional training of the CloudSkimmer agent.
        self.spawned_enemy_groups.append(CloudSkimmerGroup(self.config, x=1000, y=350))

    def spawn_skydart(self):
        # TODO implement this
        self.spawned_enemy_groups.append(SkyDartGroup(self.config, x=1000, y=100, target=self.env.player))

    def spawn_aerothief(self):
        # TODO implement this
        pass
