import math
import random

from src.utils import GameConfig, Animation
from src.entities import ItemInitializer, Player
from .enemy import Enemy, EnemyGroup


# As cool as these Ghosts would be, unless we change Cloudskimmer's skin, I won't add Ghosts, as
#  it doesn't make sense to have two different enemies that act completely differently with the same skin.


class Ghost(Enemy):
    def __init__(self, config: GameConfig, *args, **kwargs):
        super().__init__(config, Animation(config.images.enemies['cloudskimmer']), *args, **kwargs)
        self.eyes = config.images.enemies['cloudskimmer-eyes'][0]
        self.time = 0
        self.initial_y = self.y
        self.vel_x = -8
        self.initial_vel_x = self.vel_x
        self.set_max_hp(60)
        self.target_x = None
        self.target_y = None

    def tick(self):
        if self.running:
            self.time += 1
            self.x += self.vel_x
            if self.target_x is not None and self.target_y is not None:
                self.y += (self.target_y - self.y) * 0.05
        super().tick()
        self.update_eyes()

    def stop_advancing(self) -> None:
        self.vel_x = 0

    def slow_down(self, total_distance: int, remaining_distance: float) -> None:
        self.vel_x = round(self.initial_vel_x * ((remaining_distance + 25) / (total_distance + 25)))

    def launch(self):
        self.vel_x = self.initial_vel_x

    def set_target(self, target: Player) -> None:
        offset_x = random.randint(-10, 10)
        offset_y = random.randint(-10, 10)
        self.target_x = target.x + offset_x
        self.target_y = target.y + offset_y

    def update_eyes(self):
        """
        Draws the bird's eyes on the screen.
        The vertical offset is interpolated based on the player's position.
        """
        # obviously this code is not OK
        # if self.target_x is None or self.target_y is None:
        #     return
        # max_offset = 5
        # angle_from_player = math.degrees(math.atan2(self.target_y - self.y, self.target_x - self.x))
        # vertical_offset = (angle_from_player / 60) * max_offset
        # self.config.screen.blit(self.eyes, (self.x, self.y + vertical_offset))
        pass



class GhostGroup(EnemyGroup):
    def __init__(self, config: GameConfig, x: int, y: int, target: Player, *args, **kwargs):
        self.item_initializer = ItemInitializer(config, None)
        super().__init__(config, x, y, *args, **kwargs)
        self.target = target  # to get player's position in order to target it
        self.in_position = False
        self.STOP_DISTANCE = 920
        self.SLOW_DOWN_DISTANCE = 710
        self.launch_delay = 0

    def spawn_members(self) -> None:
        positions = [(self.x + 60, self.y - 95),
                     (self.x, self.y),
                     (self.x + 60, self.y + 92),
                     (self.x + 30, self.y + 45),
                     (self.x + 90, self.y)]

        for i, pos in enumerate(positions):
            member = Ghost(self.config, x=pos[0], y=pos[1], pos_id=i)
            self.members.append(member)

    def tick(self):
        if self.in_position:
            self.launch_delay += 1
            # Option 1:
            # if self.launch_delay % 4 == 0:
            #     random.shuffle(self.members)
            # Option 2:
            if self.launch_delay % 30 == 0:
                for member in self.members:
                    member.set_target(self.target)
                    member.launch()
                    break
        else:
            if self.members and self.members[0].x < self.SLOW_DOWN_DISTANCE:
                for member in self.members:
                    member.slow_down(self.SLOW_DOWN_DISTANCE - self.STOP_DISTANCE, self.members[0].x - self.STOP_DISTANCE)
                if self.members[0].x < self.STOP_DISTANCE:
                    self.in_position = True
                    for member in self.members:
                        member.stop_advancing()

        super().tick()
