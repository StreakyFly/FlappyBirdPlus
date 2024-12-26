from src.utils import GameConfig
from .enemy import EnemyGroup
from .cloudskimmer import CloudSkimmerGroup
from .skydart import SkyDartGroup


class EnemyManager:
    def __init__(self, config: GameConfig):
        self.config = config
        self.spawned_enemy_groups = []  # some files expect this list to contain no more than one enemy group at once

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
        if self.spawned_enemy_groups:
            return False
        # TODO implement this
        return True

    def spawn_enemy(self) -> None:
        # TODO implement this
        # self.spawn_cloudskimmer()  # temporary
        self.spawn_skydart()  # temporary

    def spawn_cloudskimmer(self):
        # TODO play sound effect when spawning enemy, for this one some ghost sound effect

        # Warning! Changing the x and y position will require additional training of the CloudSkimmer agent.
        self.spawned_enemy_groups.append(CloudSkimmerGroup(self.config, x=1000, y=350))

    def spawn_skydart(self):
        # TODO implement this
        self.spawned_enemy_groups.append(SkyDartGroup(self.config, x=1000, y=100))

    def spawn_aerothief(self):
        # TODO implement this
        pass
