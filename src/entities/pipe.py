import random

from src.utils import GameConfig
from .entity import Entity


class Pipe(Entity):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.vel_x = -7.5

    def tick(self) -> None:
        self.x += self.vel_x
        super().tick()


class Pipes(Entity):
    def __init__(self, config: GameConfig) -> None:
        super().__init__(config)
        self.vertical_gap: int = 225
        self.horizontal_gap: int = 390
        self.upper: list[Pipe] = []
        self.lower: list[Pipe] = []
        self.spawn_initial_pipes()

    def tick(self) -> None:
        self.manage_pipes()

        # Commented code is to determine corner low/high X values (for observation space)
        #  Y values should not be taken from here but from upper_pipe_bottom_y logic in make_random_pipes() method
        # for i, (up_pipe, low_pipe) in enumerate(zip(self.upper, self.lower)):
        for up_pipe, low_pipe in zip(self.upper, self.lower):
            # print(f"{i}: {up_pipe.x}, {up_pipe.y + up_pipe.h}, {up_pipe.x + up_pipe.w}, {up_pipe.y + up_pipe.h} | {low_pipe.x}, {low_pipe.y}, {low_pipe.x + low_pipe.w}, {low_pipe.y}")
            up_pipe.tick()
            low_pipe.tick()
            # print(f"{i}: {up_pipe.x}, {up_pipe.y + up_pipe.h}, {up_pipe.x + up_pipe.w}, {up_pipe.y + up_pipe.h} | {low_pipe.x}, {low_pipe.y}, {low_pipe.x + low_pipe.w}, {low_pipe.y}")

    def draw(self) -> None:
        for up_pipe, low_pipe in zip(self.upper, self.lower):
            up_pipe.draw()
            low_pipe.draw()

    def stop(self) -> None:
        for pipe in self.upper + self.lower:
            pipe.vel_x = 0

    def clear(self) -> None:
        """
        Removes all pipes from the environment.
        """
        self.upper = []
        self.lower = []

    def spawn_initial_pipes(self):
        pipe_x = self.config.window.width + self.horizontal_gap
        self.spawn_new_pipes(pipe_x)

        for i in range(3):
            pipe_x = self.upper[-1].x + self.horizontal_gap
            self.spawn_new_pipes(pipe_x)

    def spawn_initial_pipes_like_its_midgame(self):
        """
        Method solely for training purposes.
        Enemies don't spawn immediately at the beginning of the game, but a bit later.
        So in order to skip the beginning of the game, we need to spawn pipes as if it's mid-game.
        """
        self.upper = []
        self.lower = []

        # possible x position of the first pipe mid-game: -330 to 52.5
        self.spawn_new_pipes(self.get_random_number_divisible_by_7_5(-330, 52.5))

        for i in range(3):
            pipe_x = self.upper[-1].x + self.horizontal_gap
            self.spawn_new_pipes(pipe_x)

    @staticmethod
    def get_random_number_divisible_by_7_5(min_value: int | float, max_value: int | float) -> float:
        steps = (max_value - min_value) / 7.5
        random_step = random.randint(0, int(steps))
        random_number = min_value + (random_step * 7.5)
        return random_number

    def manage_pipes(self):
        extra = self.horizontal_gap * 0.5  # so the bullets can bounce off the pipe a bit longer after it disappears
        first_pipe = self.upper[0]
        if first_pipe.x < -first_pipe.w - extra:
            # remove the first pair of pipes if they're out of the screen
            self.upper.remove(self.upper[0])
            self.lower.remove(self.lower[0])

            # spawn a new pair of pipes self.horizontal_gap pixels away from the last pipe
            pipe_x = self.upper[-1].x + self.horizontal_gap
            self.spawn_new_pipes(x=pipe_x)

    def spawn_new_pipes(self, x: int | float = None) -> None:
        upper, lower = self.make_random_pipes(x)
        self.upper.append(upper)
        self.lower.append(lower)

    def make_random_pipes(self, x: int = None):
        base_y = self.config.window.viewport_height

        # at what y does the gap start at top (gap_y is top line, gap_y + self.pipe_gap is bottom line)
        upper_pipe_bottom_y = random.randrange(0, int(base_y * 0.6 - self.vertical_gap)) + int(base_y * 0.2)
        pipe_height = self.config.images.pipe[0].get_height()
        pipe_x = x if x is not None else self.config.window.width + 10

        upper_pipe = Pipe(self.config, self.config.images.pipe[0], pipe_x, upper_pipe_bottom_y - pipe_height)
        lower_pipe = Pipe(self.config, self.config.images.pipe[1], pipe_x, upper_pipe_bottom_y + self.vertical_gap)

        return upper_pipe, lower_pipe
