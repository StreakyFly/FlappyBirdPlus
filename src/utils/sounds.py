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

    def __init__(self, num_channels: int = 50) -> None:
        pygame.mixer.set_num_channels(num_channels)
        self.muted = False
        self.global_volume = 0.5
        self.music_volume = 1.0
        self.sounds_volume = 1.0

        self.die = _load_sound('die.wav')
        self.hit = _load_sound('hit.wav')
        self.swoosh = _load_sound('swoosh.wav')
        self.point = _load_sounds('point', 2)
        self.flap = _load_sounds('flap', 2)
        self.collect_item = _load_sounds('items/collect_item', 4)

        self.all_sounds = [self.die, self.hit, self.swoosh] + self.point + self.flap + self.collect_item

    def set_muted(self, mute: bool) -> None:
        self.muted = mute

    def play(self, sound: pygame.mixer.Sound) -> None:
        if self.muted:
            return
        sound.play()

    def play_random(self, sounds: List[pygame.mixer.Sound]) -> None:
        self.play(random.choice(sounds))

    def set_global_volume(self, volume: float) -> None:
        self.set_muted(volume == 0)
        self.global_volume = volume
        self.set_music_volume()
        self.set_sounds_volume()

    def set_music_volume(self, volume: float = None) -> None:
        if volume is not None:
            self.music_volume = volume
        new_volume = self.global_volume * self.music_volume
        pygame.mixer.music.set_volume(new_volume)

    def set_sounds_volume(self, volume: float = None) -> None:
        if volume is not None:
            self.sounds_volume = volume
        new_volume = self.global_volume * self.sounds_volume
        for sound in self.all_sounds:
            sound.set_volume(new_volume)


def _load_sound(sound_name: str) -> pygame.mixer.Sound:
    return pygame.mixer.Sound(f'assets/audio/{sound_name}')


def _load_item_sound(sound_name: str) -> pygame.mixer.Sound:
    return _load_sound(f'items/{sound_name}')


def _load_sounds(sound_name: str, count: int) -> List[pygame.mixer.Sound]:
    sounds = []
    for num in range(1, count + 1):
        sounds.append(_load_sound(f'{sound_name}_{num}.wav'))
    return sounds
