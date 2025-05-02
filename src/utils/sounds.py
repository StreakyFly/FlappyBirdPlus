import random
from abc import ABC, abstractmethod
from typing import List, Dict

import pygame


# TODO:
#  - add sound effects and music volume sliders in settings menu
#  - play some chill/happy music in main menu, when the game starts, start the main theme, when player dies, stop
#  - maybe alternate between a couple of tracks, so you don't get sick of the same track
#  - different soundtrack for packman of course
#  - maybe some extra sounds when enemies appear, to make it more dramatic

class BaseSounds(ABC):
    @abstractmethod
    def set_muted(self, mute: bool) -> None: pass

    @abstractmethod
    def play(self, sound): pass

    @abstractmethod
    def play_random(self, sounds): pass

    @abstractmethod
    def set_global_volume(self, volume: float) -> None: pass

    @abstractmethod
    def set_music_volume(self, volume: float = None) -> None: pass

    @abstractmethod
    def set_sounds_volume(self, volume: float = None) -> None: pass

    @staticmethod
    @abstractmethod
    def play_background_music() -> None: pass

    @staticmethod
    @abstractmethod
    def pause_background_music() -> None: pass

    @staticmethod
    @abstractmethod
    def unpause_background_music() -> None: pass


class DummySounds(BaseSounds):
    background_music: pygame.mixer.music = None
    die: pygame.mixer.Sound = None
    hit: pygame.mixer.Sound = None
    swoosh: pygame.mixer.Sound = None
    point: List[pygame.mixer.Sound] = []
    flap: List[pygame.mixer.Sound] = []
    collect_item: List[pygame.mixer.Sound] = []
    weapons: Dict[str, Dict[str, pygame.mixer.Sound]] = {
        'ak47': {'shoot': None, 'reload': None},
        'deagle': {'shoot': None, 'reload': None},
        'uzi': {'shoot': None, 'reload': None}
    }
    hit_quiet: pygame.mixer.Sound = None
    hit_bullet: pygame.mixer.Sound = None

    def set_muted(self, mute: bool): pass
    def play(self, sound): pass
    def play_random(self, sounds): pass
    def set_global_volume(self, volume): pass
    def set_music_volume(self, volume=None): pass
    def set_sounds_volume(self, volume=None): pass
    @staticmethod
    def play_background_music(): pass
    @staticmethod
    def pause_background_music(): pass
    @staticmethod
    def unpause_background_music(): pass


class Sounds(BaseSounds):
    background_music: pygame.mixer.music
    die: pygame.mixer.Sound
    hit: pygame.mixer.Sound
    swoosh: pygame.mixer.Sound
    point: List[pygame.mixer.Sound]
    flap: List[pygame.mixer.Sound]
    collect_item: List[pygame.mixer.Sound]
    weapons: Dict[str, Dict[str, pygame.mixer.Sound]]
    # TODO: refactor this, maybe put all hit sounds in a dict?
    hit_quiet: pygame.mixer.Sound
    hit_bullet: pygame.mixer.Sound

    def __init__(self, volume: float = 0.5) -> None:
        self.muted = False
        pygame.mixer.set_num_channels(50)
        self.global_volume = volume
        self.music_volume = 1.0
        self.sounds_volume = 1.0

        self._load_base_sounds()
        self._load_weapon_sounds()

        self.all_sounds = [self.die, self.hit, self.swoosh, self.hit_quiet] + self.point + self.flap + self.collect_item + \
                          [sound for weapon_sounds in self.weapons.values() for sound in weapon_sounds.values()]

        self.set_global_volume(volume)

    def set_muted(self, mute: bool) -> None:
        self.muted = mute
        if mute:
            self.pause_background_music()
        else:
            self.unpause_background_music()

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

    @staticmethod
    def play_background_music() -> None:
        pygame.mixer.music.play(-1)

    @staticmethod
    def pause_background_music() -> None:
        pygame.mixer.music.pause()

    @staticmethod
    def unpause_background_music() -> None:
        pygame.mixer.music.unpause()

    def _load_base_sounds(self) -> None:
        self.background_music = _load_music('background_music')
        self.die = _load_sound('die')
        self.hit = _load_sound('hit')
        self.swoosh = _load_sound('swoosh')
        self.point = _load_sounds('point', 2)
        self.flap = _load_sounds('flap', 2)
        self.collect_item = _load_sounds('items/collect_item', 4)
        self.hit_quiet = _load_sound('hit_quiet')
        self.hit_bullet = _load_item_sound('hit_bullet')

    def _load_weapon_sounds(self) -> None:
        self.weapons = {}
        weapon_names = ('ak47', 'deagle', 'uzi')

        for weapon_name in weapon_names:
            self.weapons[weapon_name] = {
                'shoot': _load_item_sound(f'weapons/{weapon_name}-shoot'),
                'reload': _load_item_sound(f'weapons/{weapon_name}-reload')
            }

def _load_sound(sound_name: str, extension: str = 'wav') -> pygame.mixer.Sound:
    return pygame.mixer.Sound(f'assets/audio/sfx/{sound_name}.{extension}')


def _load_music(music_name: str, extension: str = 'mp3') -> pygame.mixer.music:
    return pygame.mixer.music.load(f'assets/audio/music/{music_name}.{extension}')


def _load_item_sound(sound_name: str) -> pygame.mixer.Sound:
    return _load_sound(f'items/{sound_name}')


def _load_sounds(sound_name: str, count: int, extension: str = 'wav') -> List[pygame.mixer.Sound]:
    sounds = []
    for num in range(1, count + 1):
        sounds.append(_load_sound(f'{sound_name}_{num}', extension))
    return sounds
