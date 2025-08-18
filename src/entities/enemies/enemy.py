from src.entities import ItemName
from src.entities.attribute_bar import AttributeBar
from src.entities.entity import Entity
from src.utils import GameConfig, Animation


class Enemy(Entity):
    heal_on_kill: int = 0  # amount of shield to reward the player, when they kill this enemy

    def __init__(
            self,
            config: GameConfig,
            animation: Animation,
            instance_id: int,
            possible_drop_items: list[ItemName],  # items that this enemy can drop when killed
            *args, **kwargs
        ):
        super().__init__(config, *args, **kwargs)
        self.animation: Animation = animation
        self.update_image(self.animation.update())

        self.vel_x: float = 0
        self.vel_y: float = 0
        self.rotation: float = 0

        self.hp_bar = AttributeBar(config=self.config, max_value=100, color=(255, 0, 0, 222), x=self.x, y=int(self.y) - 25, w=self.w, h=10)

        self.id: int = instance_id
        self.is_gone = False  # whether the enemy has finished its death animation and is ready to be removed from the game
        self.running: bool = True  # whether the enemy is currently running or is stopped

        self.possible_drop_items: list[ItemName] = possible_drop_items

    def tick(self):
        # self.is_gone might be set to True from outside, so we check it first
        if self.is_gone or self.x < -200:
            self.is_gone = True
            return

        if self.running:
            self.update_image(self.animation.update())

        self.hp_bar.y = self.y - 25
        self.hp_bar.x = self.x
        self.hp_bar.tick()
        super().tick()

    def stop(self) -> None:
        self.running = False

    def set_max_hp(self, max_value: int) -> None:
        self.hp_bar.max_value = max_value
        self.hp_bar.current_value = max_value

    def deal_damage(self, amount: int) -> None:
        self.hp_bar.change_value_by(-amount)

        if self.hp_bar.is_empty() and not self.is_gone:
            self.die()

    def die(self) -> None:
        # TODO play death sound
        self.play_death_animation()

    def play_death_animation(self) -> None:
        # TODO implement this

        # death animation code

        # if death animation is done set is_gone to True
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
        self.spawn_members()

    def tick(self):
        for member in set(self.members):
            member.tick()
            if member.is_gone:
                self.members.remove(member)
                self.on_member_death(member)

    def stop(self) -> None:
        for member in self.members:
            member.stop()

    def is_empty(self) -> bool:
        return not self.members

    def on_member_death(self, member: Enemy) -> None:
        """
        This method is called when a member of the group dies.
        It can be overridden in subclasses to implement specific behavior on member death.
        """
        pass

    def spawn_members(self) -> None:
        raise NotImplementedError("spawn_members method must be implemented in subclass")
