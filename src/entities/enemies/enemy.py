import pygame

from ...utils import GameConfig, Animation
from ..entity import Entity
from ..attribute_bar import AttributeBar


class Enemy(Entity):
    BACKGROUND_VELOCITY = pygame.Vector2(-7.5, 0)

    def __init__(self, config: GameConfig, animation: Animation, *args, **kwargs):
        super().__init__(config, *args, **kwargs)
        self.animation: Animation = animation
        self.update_image(self.animation.update())
        self.hp_manager = AttributeBar(config=self.config, max_value=150, color=(255, 0, 0, 222),
                                       x=self.x, y=int(self.y) - 25, w=self.w, h=10)
        self.is_gone = False

    def tick(self):
        if self.x < -200:
            self.is_gone = True

        self.update_image(self.animation.update())

        self.hp_manager.y = self.y - 25
        self.hp_manager.x = self.x
        self.hp_manager.tick()
        super().tick()

    def change_life(self, amount: int) -> None:
        self.hp_manager.change_value(amount)

        if self.hp_manager.is_empty() and not self.is_gone:
            self.die()

    def die(self) -> None:
        # TODO play death sound
        self.play_death_animation()

    def play_death_animation(self) -> None:
        # TODO implement this

        self.is_gone = True

    def play_spawn_animation(self) -> None:
        # TODO implement this
        pass


class EnemyGroup:
    def __init__(self, config: GameConfig, x: int, y: int, *args, **kwargs):
        self.config = config
        self.x = x
        self.y = y
        self.members = []

    def tick(self):
        for member in self.members:
            if member.is_gone:
                self.members.remove(member)
            member.tick()

    def is_empty(self) -> bool:
        return not self.members

    def spawn_enemy(self, animation: Animation) -> None:
        # TODO implement this
        # self.members.append(Enemy(self.config, animation, x=self.x, y=self.y))
        pass
