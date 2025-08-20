import random

from src.utils import GameConfig
from .cloudskimmer import CloudSkimmerGroup
from .skydart import SkyDartGroup


class EnemyManager:
    def __init__(self, config: GameConfig, env):
        self.config = config
        self.env = env
        self.spawned_enemy_groups = []  # [WARN]: Most parts of the codebase expect this list to contain max one group at a time.
        self.wait = random.randint(240, 420)
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
        if self.spawned_enemy_groups:
            return False

        if self.wait <= 0:
            self.wait = random.randint(240, 420)
            return True

        self.wait -= 1
        return False

    def spawn_enemy(self) -> None:
        self.group_to_spawn()
        self.group_to_spawn = random.choice([self.spawn_skydart, self.spawn_cloudskimmer])

    def spawn_cloudskimmer(self):
        # TODO play sound effect when spawning enemy - for this one some ghost sound effect
        # Warning! Changing the x and y position will require additional training of the CloudSkimmer agent.
        self.spawned_enemy_groups.append(CloudSkimmerGroup(self.config, x=1000, y=350, env=self.env))

    def spawn_skydart(self):
        # TODO implement this
        self.spawned_enemy_groups.append(SkyDartGroup(self.config, x=1000, y=0, target=self.env.player))

    def spawn_aerothief(self):
        # TODO implement this
        pass
