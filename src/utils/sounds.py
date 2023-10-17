import pygame


class Sounds:
    die: pygame.mixer.Sound
    hit: pygame.mixer.Sound
    point: pygame.mixer.Sound
    swoosh: pygame.mixer.Sound
    wing: pygame.mixer.Sound

    def __init__(self) -> None:
        self.die = _load_sound('die.wav')
        self.hit = _load_sound('hit.wav')
        self.point = _load_sound('point.wav')
        self.swoosh = _load_sound('swoosh.wav')
        self.wing = _load_sound('wing.wav')


def _load_sound(path):
    return pygame.mixer.Sound(f'assets/audio/{path}')
