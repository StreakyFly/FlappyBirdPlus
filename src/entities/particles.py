import math
import random

import pygame

from .entity import Entity
from src.utils import GameConfig, get_random_value


class Particle(Entity):
    def __init__(self, config: GameConfig, x, y, lifespan: int, gravity: float = 0.05, initial_velocity: pygame.Vector2 = None,
                 radius: int = 20, color: tuple = (255, 255, 255), **kwargs):
        super().__init__(config=config, x=x, y=y, **kwargs)
        self.lifespan = lifespan
        self.age: int = 0
        self.color = color
        self.initial_radius = radius
        self.radius = radius
        self.gravity = gravity
        self.velocity: pygame.Vector2 = initial_velocity or pygame.Vector2(random.uniform(-1, 1), random.uniform(-5, -2))

    def tick(self):
        self.age += 1
        self.x += self.velocity.x
        self.y += self.velocity.y
        self.velocity.y += self.gravity

        # TODO: improve the particle decay formula - currently the end is a bit sudden
        # Exponential decay for the radius
        decay_factor = math.exp(-self.age / self.lifespan)  # Exponential decay based on age/lifespan
        self.radius = max(1, int(self.initial_radius * decay_factor))  # Keeps radius from reaching 0 too early

        super().tick()

    def draw(self):
        """Draw the particle as a pixelated circle."""
        pixel_size = 5  # size of each 'pixel' (block)
        radius = self.radius
        x, y = int(self.x), int(self.y)

        surface = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
        surface = surface.convert_alpha()

        # Loop through the area that the circle occupies
        for dx in range(-radius, radius + 1, pixel_size):
            for dy in range(-radius, radius + 1, pixel_size):
                # Check if the (dx, dy) position is inside the circle's area
                if dx**2 + dy**2 <= radius**2:
                    pygame.draw.rect(surface, self.color, pygame.Rect(dx + radius - pixel_size // 2, dy + radius - pixel_size // 2, pixel_size, pixel_size))

        self.config.screen.blit(surface, (x - radius, y - radius))


    def is_alive(self):
        return self.age < self.lifespan


class ParticleManager:
    def __init__(self, config: GameConfig):
        self.config = config
        self.particles = set()

    def tick(self):
        if not self.particles:
            return

        for particle in set(self.particles):
            particle.tick()
            if not particle.is_alive():
                self.particles.remove(particle)

    # Nghhmmmmm, what other types should the parameters support? 🥰
    def spawn_particles(self, x, y,
                        count: int | tuple | list = (10, 20),
                        lifespan: int | tuple | list = (40, 60),
                        radius: int | float | tuple | list = (10, 20),
                        gravity: int | float | tuple | list =(0.1, 0.2),
                        position_offset_x: int | float | tuple | list = 0,
                        position_offset_y: int | float | tuple | list = 0,
                        initial_velocity_x: int | float | tuple | list = (-5, 5),
                        initial_velocity_y: int | float | tuple | list = (-5, 5),
                        color: tuple | tuple[tuple] = (255, 255, 255, 255)
                        ):
        """Spawn multiple particles around the given position with random properties."""
        for _ in range(get_random_value(count, random_type="range", as_int=True)):
            particle = Particle(
                config=self.config,
                x=x + get_random_value(position_offset_x, random_type="auto", as_int=True),
                y=y + get_random_value(position_offset_y, random_type="auto", as_int=True),
                lifespan=get_random_value(lifespan, random_type="auto", as_int=True),
                radius=get_random_value(radius, random_type="auto", as_int=False),
                gravity=get_random_value(gravity, random_type="auto", as_int=False),
                initial_velocity=pygame.Vector2(
                    get_random_value(initial_velocity_x, random_type="auto", as_int=False),
                    get_random_value(initial_velocity_y, random_type="auto", as_int=False),
                ),
                color=tuple([get_random_value(c) for c in color]),
            )
            self.particles.add(particle)
