import random
from typing import List

from ..utils import GameConfig
from .entity import Entity


class Pipe(Entity):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.vel_x = -7.5

    def draw(self) -> None:
        self.x += self.vel_x
        super().draw()


class Pipes(Entity):
    upper: List[Pipe]
    lower: List[Pipe]
    pipe_gap: int

    def __init__(self, config: GameConfig) -> None:
        super().__init__(config)
        self.pipe_gap = 225
        self.top = 0
        self.bottom = self.config.window.viewport_height
        self.upper = []
        self.lower = []
        self.spawn_initial_pipes()

    def tick(self) -> None:
        if self.can_spawn_pipes():
            self.spawn_new_pipes()
        self.remove_old_pipes()

        for up_pipe, low_pipe in zip(self.upper, self.lower):
            up_pipe.tick()
            low_pipe.tick()

    def stop(self) -> None:
        for pipe in self.upper + self.lower:
            pipe.vel_x = 0

    def can_spawn_pipes(self) -> bool:
        last = self.upper[-1]
        return self.config.window.width - (last.x + last.w) > last.w * 1.9

    def spawn_new_pipes(self):
        # add new pipe when first pipe is about to touch left of screen
        upper, lower = self.make_random_pipes()
        self.upper.append(upper)
        self.lower.append(lower)

    def remove_old_pipes(self):
        # remove first pipe if it's out of the screen
        for pipe in self.upper:
            if pipe.x < -pipe.w:
                self.upper.remove(pipe)

        for pipe in self.lower:
            if pipe.x < -pipe.w:
                self.lower.remove(pipe)

    def spawn_initial_pipes(self):
        upper_1, lower_1 = self.make_random_pipes()
        upper_1.x = self.config.window.width + upper_1.w * 3
        lower_1.x = self.config.window.width + upper_1.w * 3
        self.upper.append(upper_1)
        self.lower.append(lower_1)

    def make_random_pipes(self):
        base_y = self.config.window.viewport_height

        # at what y does the gap start at top (gap_y is top line, gap_y + self.pipe_gap is bottom line)
        gap_y = random.randrange(0, int(base_y * 0.6 - self.pipe_gap)) + int(base_y * 0.2)
        pipe_height = self.config.images.pipe[0].get_height()
        pipe_x = self.config.window.width + 10

        upper_pipe = Pipe(self.config, self.config.images.pipe[0], pipe_x, gap_y - pipe_height)
        lower_pipe = Pipe(self.config, self.config.images.pipe[1], pipe_x, gap_y + self.pipe_gap)

        return upper_pipe, lower_pipe
