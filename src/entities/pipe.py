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
    vertical_gap: int
    horizontal_gap: int

    def __init__(self, config: GameConfig) -> None:
        super().__init__(config)
        self.vertical_gap = 225
        self.horizontal_gap = 390
        self.top = 0
        self.bottom = self.config.window.viewport_height
        self.upper = []
        self.lower = []
        self.spawn_initial_pipes()

    def tick(self) -> None:
        self.manage_pipes()

        for up_pipe, low_pipe in zip(self.upper, self.lower):
            up_pipe.tick()
            low_pipe.tick()

    def stop(self) -> None:
        for pipe in self.upper + self.lower:
            pipe.vel_x = 0

    def spawn_new_pipes(self, x: int = None) -> None:
        upper, lower = self.make_random_pipes(x)
        self.upper.append(upper)
        self.lower.append(lower)

    def manage_pipes(self):
        # remove the first pair of pipes if they're out of the screen
        extra = self.upper[0].w * 1.5
        for num, pipe in enumerate(self.upper):
            if pipe.x < -pipe.w - extra:
                self.upper.remove(pipe)
                self.lower.remove(self.lower[num])

                # spawn a new pair of pipes self.horizontal_gap pixels away from the last pipe
                pipe_x = self.upper[-1].x + self.horizontal_gap
                self.spawn_new_pipes(x=pipe_x)
                break  # there shouldn't be multiple pipes out of the screen at once, so no need to check the rest

    def spawn_initial_pipes(self):
        pipe_x = self.config.window.width + self.horizontal_gap
        self.spawn_new_pipes(pipe_x)

        for i in range(3):
            pipe_x = self.upper[-1].x + self.horizontal_gap
            self.spawn_new_pipes(pipe_x)

    def make_random_pipes(self, x: int = None):
        base_y = self.config.window.viewport_height

        # at what y does the gap start at top (gap_y is top line, gap_y + self.pipe_gap is bottom line)
        gap_y = random.randrange(0, int(base_y * 0.6 - self.vertical_gap)) + int(base_y * 0.2)
        pipe_height = self.config.images.pipe[0].get_height()
        pipe_x = x or self.config.window.width + 10

        upper_pipe = Pipe(self.config, self.config.images.pipe[0], pipe_x, gap_y - pipe_height)
        lower_pipe = Pipe(self.config, self.config.images.pipe[1], pipe_x, gap_y + self.vertical_gap)

        return upper_pipe, lower_pipe
