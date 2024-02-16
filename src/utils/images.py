import random
from typing import Tuple, List, Dict

import pygame


class Images:
    background: pygame.Surface
    floor: pygame.Surface
    pipe: Tuple[pygame.Surface, pygame.Surface]
    player: Tuple[pygame.Surface, pygame.Surface, pygame.Surface]
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
        PLAYER_IMGS = [['yellowbird-upflap', 'yellowbird-midflap', 'yellowbird-downflap'],
                       ['bluebird-upflap', 'bluebird-midflap', 'bluebird-downflap'],
                       ['redbird-upflap', 'redbird-midflap', 'redbird-downflap']]

        random_player = random.randint(0, len(PLAYER_IMGS) - 1)

        self.player = (_load_image(f'player/{PLAYER_IMGS[random_player][0]}'),
                       _load_image(f'player/{PLAYER_IMGS[random_player][1]}'),
                       _load_image(f'player/{PLAYER_IMGS[random_player][2]}'))

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
        item_type_names = ('empty', 'empty-weapon', 'empty-ammo', 'empty-potion', 'empty-heal', 'empty-special',
                           'weapon', 'ammo', 'potion', 'heal', 'special')
        for item_type in item_type_names:
            self.inventory_backgrounds[item_type] = _load_item_image(f'inventory_backgrounds/{item_type}').convert()

    def _load_item_images(self) -> None:
        self.items = dict()
        item_names = (
            'empty/empty', 'empty/empty-weapon', 'empty/empty-ammo',
            'special/totem-of-undying', 'heals/medkit', 'heals/bandage', 'potions/potion-heal', 'potions/potion-shield',

        )
        item_names += _get_armament_names()

        for item in item_names:
            item_name = item.split('/')[-1]
            self.items[item_name] = _load_item_image(item).convert_alpha()

            for version in ('_small', '_inventory'):
                try:
                    self.items[f"{item_name}{version}"] = _load_item_image(f'{item}{version}').convert_alpha()
                except FileNotFoundError:
                    pass

    def _load_enemy_images(self) -> None:
        self.enemies = dict()
        enemy_names = ('enemy-temp_1', 'enemy-temp_2', )

        for enemy_name in enemy_names:
            base_name = enemy_name.rsplit('_', 1)[0]
            if base_name not in self.enemies:
                self.enemies[base_name] = []
            self.enemies[base_name].append(_load_image(f'enemies/{enemy_name}').convert_alpha())


def _load_image(image_name) -> pygame.Surface:
    return pygame.image.load(f'assets/images/{image_name}.png')


def _load_item_image(item_name) -> pygame.Surface:
    return _load_image(f'items/{item_name}')


def _get_armament_names() -> Tuple[str]:
    DIR_PREFIXES = ['weapons', 'weapons/ammo']
    weapons = ('ak-47', 'deagle', 'uzi', )
    ammunition = ('ammo-box', 'small-bullet', 'medium-bullet', 'big-bullet', )

    names = [f'{DIR_PREFIXES[0]}/{weapon}' for weapon in weapons]
    names.extend([f'{DIR_PREFIXES[1]}/{ammo}' for ammo in ammunition])

    return tuple(names)
