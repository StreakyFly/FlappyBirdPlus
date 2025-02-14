import pygame


class Sounds:
    theme: pygame.mixer.Sound
    soundtrack: pygame.mixer.Sound
    die: pygame.mixer.Sound
    eat_pellet: pygame.mixer.Sound
    eat_fruit: pygame.mixer.Sound
    eat_ghost: pygame.mixer.Sound
    power_up: pygame.mixer.Sound

    def __init__(self, volume: float = 1) -> None:
        self.sounds_volume = volume
        self.theme = _load_sound('theme', 'mp3')
        self.soundtrack = _load_sound('soundtrack')
        self.die = _load_sound('die')
        self.eat_pellet = _load_sound('eat_pellet')
        self.eat_fruit = _load_sound('eat_fruit')
        self.eat_ghost = _load_sound('eat_ghost')
        self.power_up = _load_sound('power_up')

        self.all_sounds = [self.theme, self.soundtrack, self.die, self.eat_pellet, self.eat_fruit, self.eat_ghost, self.power_up]

        # Set volume for all sounds
        for sound in self.all_sounds:
            sound.set_volume(self.sounds_volume)


def _load_sound(sound_name: str, extension: str = 'wav') -> pygame.mixer.Sound:
    return pygame.mixer.Sound(f'assets/audio/pacman/{sound_name}.{extension}')
