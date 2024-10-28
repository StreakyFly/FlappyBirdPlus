import random
from typing import Tuple, List, Dict

import pygame


class Images:
    background: pygame.Surface
    floor: pygame.Surface
    pipe: Tuple[pygame.Surface, pygame.Surface]
    player: Tuple[pygame.Surface, ...]
    welcome_message: pygame.Surface
    game_over: pygame.Surface
    inventory_slot: pygame.Surface
    item_spawn_bubble: pygame.Surface
    inventory_backgrounds: Dict[str, pygame.Surface]
    items: Dict[str, pygame.Surface]
    enemies: Dict[str, List[pygame.Surface]]

    def __init__(self) -> None:
        self._load_base_images()
        self._load_inventory_backgrounds()
        self._load_item_images()
        self._load_enemy_images()

    def randomize(self) -> None:
        PLAYER_IMG_NAMES = ('bird-yellow', 'bird-blue', 'bird-red')

        random_player_index = random.randint(0, len(PLAYER_IMG_NAMES) - 1)
        player_spritesheet = _load_image(f'player/{PLAYER_IMG_NAMES[random_player_index]}', True)

        self.player = tuple(_animation_spritesheet_to_frames(player_spritesheet, 3))

    def _load_base_images(self) -> None:
        self.background = _load_image('background-day').convert()
        self.floor = _load_image('floor').convert_alpha()
        self.pipe = (pygame.transform.flip(_load_image('pipe').convert_alpha(), False, True),
                     _load_image('pipe').convert_alpha())
        self.welcome_message = _load_image('welcome-message').convert_alpha()
        self.game_over = _load_image('game-over').convert_alpha()
        self.inventory_slot = _load_image('inventory-slot').convert_alpha()
        self.item_spawn_bubble = _load_image('item-spawn-bubble').convert_alpha()
        self.randomize()

    def _load_inventory_backgrounds(self) -> None:
        self.inventory_backgrounds = dict()
        ITEM_TYPE_NAMES = ('empty', 'empty-weapon', 'empty-ammo', 'empty-potion', 'empty-heal', 'empty-special',
                           'weapon', 'ammo', 'potion', 'heal', 'special')
        for item_type in ITEM_TYPE_NAMES:
            self.inventory_backgrounds[item_type] = _load_image(_items_dir(f'inventory_backgrounds/{item_type}')).convert()

    def _load_item_images(self) -> None:
        self.items = dict()
        item_names = (
            'empty/empty', 'empty/empty-weapon', 'empty/empty-ammo',
            'special/totem-of-undying', 'heals/medkit', 'heals/bandage', 'potions/potion-heal', 'potions/potion-shield',
        )
        item_names += _get_armament_names()

        for item in item_names:
            item_name = item.split('/')[-1]
            self.items[item_name] = _load_image(_items_dir(item)).convert_alpha()

            for version in ('small', 'inventory'):
                try:
                    self.items[f"{item_name}_{version}"] = _load_image(_items_dir(f'{item}_{version}')).convert_alpha()
                except FileNotFoundError:
                    pass

    def _load_enemy_images(self) -> None:
        self.enemies = dict()
        ENEMY_IMG_NAMES = ('enemy-cloudskimmer_1', 'enemy-cloudskimmer-eyes')

        for enemy_name in ENEMY_IMG_NAMES:
            base_name = enemy_name.rsplit('_', 1)[0]
            if base_name not in self.enemies:
                self.enemies[base_name] = []
            self.enemies[base_name].append(_load_image(f'enemies/{enemy_name}').convert_alpha())


def _load_image(image_name: str, is_spritesheet: bool = False) -> pygame.Surface:
    suffix = '_spritesheet' if is_spritesheet else ''
    return pygame.image.load(f'assets/images/{image_name}{suffix}.png')


def _items_dir(item_name: str) -> str:
    return f'items/{item_name}'


def _get_armament_names() -> Tuple[str, ...]:
    DIR_PREFIXES = ['weapons', 'weapons/ammo']
    WEAPON_NAMES = ('ak-47', 'deagle', 'uzi', )
    AMMUNITION_NAMES = ('ammo-box', 'small-bullet', 'medium-bullet', 'big-bullet', )

    names = [f'{DIR_PREFIXES[0]}/{weapon}' for weapon in WEAPON_NAMES]
    names.extend([f'{DIR_PREFIXES[1]}/{ammo}' for ammo in AMMUNITION_NAMES])

    return tuple(names)


def _animation_spritesheet_to_frames(spritesheet: pygame.Surface, num_frames: int) -> List[pygame.Surface]:
    frame_width = spritesheet.get_width() // num_frames
    frame_height = spritesheet.get_height()
    frames = []

    for i in range(num_frames):
        frame = spritesheet.subsurface(pygame.Rect(i * frame_width, 0, frame_width, frame_height)).convert_alpha()
        frames.append(frame)

    return frames
