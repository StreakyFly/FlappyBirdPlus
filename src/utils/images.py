import random
from typing import Tuple, List, Dict

import pygame


class Images:
    background: pygame.Surface
    floor: pygame.Surface
    pipe: Tuple[pygame.Surface, pygame.Surface]
    player: Tuple[pygame.Surface, ...]
    player_id: int
    item_spawn_bubble: pygame.Surface
    items: Dict[str, pygame.Surface]
    enemies: Dict[str, List[pygame.Surface]]
    user_interface: Dict[str, pygame.Surface]

    def __init__(self) -> None:
        self._load_user_interface_images()
        self._load_base_images()
        self._load_item_images()
        self._load_enemy_images()

    def randomize(self) -> None:
        PLAYER_IMG_NAMES = ('bird-yellow', 'bird-blue', 'bird-red')

        random_player_index = random.randint(0, len(PLAYER_IMG_NAMES) - 1)
        player_spritesheet = load_image(f'player/{PLAYER_IMG_NAMES[random_player_index]}', True)

        self.player_id = random_player_index
        self.player = tuple(animation_spritesheet_to_frames(player_spritesheet, 3))

    def _load_user_interface_images(self) -> None:
        images_alpha_flags = {
            'welcome-message': True,
            'game-over': True,
            'menu': True,  # TODO: will it have transparent parts or nah?
            'button-wide': False,  # TODO: will it have transparent parts or nah?
            'inventory/inventory-slot': True,
            'inventory/inventory-bg-empty': False,
            'inventory/inventory-bg-taken': False,
        }
        self.user_interface = {}
        for element, alpha in images_alpha_flags.items():
            image = load_image(f'user_interface/{element}')
            self.user_interface[element.split('/')[-1]] = image.convert_alpha() if alpha else image.convert()

    def _load_base_images(self) -> None:
        self.background = load_image('background-day').convert()
        self.floor = load_image('floor').convert_alpha()
        self.pipe = (pygame.transform.flip(load_image('pipe').convert_alpha(), False, True),
                     load_image('pipe').convert_alpha())
        self.item_spawn_bubble = load_image('item-spawn-bubble').convert_alpha()
        self.randomize()

    def _load_item_images(self) -> None:
        self.items = dict()
        item_names = (
            'empty/empty', 'empty/empty-weapon', 'empty/empty-ammo', 'empty/empty-food', 'empty/empty-heal', 'empty/empty-potion', 'empty/empty-special',
            'food/apple', 'food/burger', 'food/chocolate',
            'potions/potion-heal', 'potions/potion-shield',
            'heals/medkit', 'heals/bandage',
            'special/totem-of-undying',
        )
        item_names += _get_armament_names()

        for item in item_names:
            item_name = item.split('/')[-1]
            self.items[item_name] = load_image(_items_dir(item)).convert_alpha()

            for version in ('small', 'inventory'):
                try:
                    self.items[f"{item_name}_{version}"] = load_image(_items_dir(f'{item}_{version}')).convert_alpha()
                except FileNotFoundError:
                    pass

    def _load_enemy_images(self) -> None:
        self.enemies = dict()
        ENEMY_SPRITES = {
            'cloudskimmer': 1,
            'cloudskimmer-eyes': 1,
            'skydart': 3,
        }

        for enemy_name, num_sprites in ENEMY_SPRITES.items():
            if enemy_name not in self.enemies:
                self.enemies[enemy_name] = []
            is_spritesheet = num_sprites > 1
            image = load_image(f'enemies/{enemy_name}', is_spritesheet).convert_alpha()
            if is_spritesheet:
                self.enemies[enemy_name].extend(animation_spritesheet_to_frames(image, num_sprites))
            else:
                self.enemies[enemy_name].append(image)


def _items_dir(item_name: str) -> str:
    return f'items/{item_name}'


def _get_armament_names() -> Tuple[str, ...]:
    DIR_PREFIXES = ['weapons', 'weapons/ammo']
    WEAPON_NAMES = ('ak47', 'deagle', 'uzi', )
    AMMUNITION_NAMES = ('ammo-box', 'small-bullet', 'medium-bullet', 'big-bullet', )

    names = [f'{DIR_PREFIXES[0]}/{weapon}' for weapon in WEAPON_NAMES]
    names.extend([f'{DIR_PREFIXES[1]}/{ammo}' for ammo in AMMUNITION_NAMES])

    return tuple(names)


def load_image(image_name: str, is_spritesheet: bool = False) -> pygame.Surface:
    suffix = '_spritesheet' if is_spritesheet else ''
    return pygame.image.load(f'assets/images/{image_name}{suffix}.png')


def animation_spritesheet_to_frames(spritesheet: pygame.Surface, num_frames: int) -> List[pygame.Surface]:
    frame_width = spritesheet.get_width() // num_frames
    frame_height = spritesheet.get_height()
    frames = []

    for i in range(num_frames):
        frame = spritesheet.subsurface(pygame.Rect(i * frame_width, 0, frame_width, frame_height)).convert_alpha()
        frames.append(frame)

    return frames
