import random
from typing import List

import pygame


class Sounds:
    die: pygame.mixer.Sound
    hit: pygame.mixer.Sound
    swoosh: pygame.mixer.Sound
    point: List[pygame.mixer.Sound]
    flap: List[pygame.mixer.Sound]
    collect_item: List[pygame.mixer.Sound]

    def __init__(self) -> None:
        self.die = _load_sound('die.wav')
        self.hit = _load_sound('hit.wav')
        self.swoosh = _load_sound('swoosh.wav')
        self.point = _load_sounds('point', 2)
        self.flap = _load_sounds('flap', 2)
        self.collect_item = _load_sounds('items/collect_item', 4)

    def play_random(self, sounds):
        random.choice(sounds).play()


def _load_sound(sound_name) -> pygame.mixer.Sound:
    return pygame.mixer.Sound(f'assets/audio/{sound_name}')


def _load_item_sound(sound_name) -> pygame.mixer.Sound:
    return _load_sound(f'items/{sound_name}')


def _load_sounds(sound_name, count) -> List[pygame.mixer.Sound]:
    sounds = []
    for num in range(1, count + 1):
        sounds.append(_load_sound(f'{sound_name}_{num}.wav'))
    return sounds
