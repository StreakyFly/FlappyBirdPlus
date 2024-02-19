from ...utils import GameConfig

from .cloudskimmer import CloudSkimmer


class EnemyManager:
    def __init__(self, config: GameConfig):
        self.config = config
        self.spawned_enemies = []

    def tick(self):
        if self.can_spawn_enemy():
            self.spawn_enemy()

        for enemy in self.spawned_enemies:
            if enemy.died:
                self.spawned_enemies.remove(enemy)
            enemy.tick()

    def can_spawn_enemy(self) -> bool:
        if self.spawned_enemies:
            return False
        # TODO implement this
        return True

    def spawn_enemy(self) -> None:
        # TODO implement this
        self.test_spawn_enemies()

    def test_spawn_enemies(self):
        # TODO DELETE THIS METHOD LATERR
        self.spawned_enemies.append(CloudSkimmer(self.config, x=550, y=250))
        self.spawned_enemies.append(CloudSkimmer(self.config, x=500, y=400))
        self.spawned_enemies.append(CloudSkimmer(self.config, x=550, y=550))
