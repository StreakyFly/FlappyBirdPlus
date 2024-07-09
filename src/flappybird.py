import asyncio
import os
import sys

import pygame
from pygame.locals import K_SPACE, KEYDOWN, QUIT

from .utils import GameConfig, GameState, GameStateManager, Window, Images, Sounds
from .entities import Background, Floor, Player, PlayerMode, Pipes, Score, WelcomeMessage, GameOver, \
    Inventory, ItemManager, ItemName, EnemyManager
# from .config import Config <-- imported later to avoid circular import


class FlappyBird:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Flappy Bird by @StreakyFly")
        window = Window(width=720, height=960)
        if os.environ.get('SDL_VIDEODRIVER') == 'dummy':
            screen = pygame.display.set_mode((window.width, window.height))
        else:
            screen = pygame.display.set_mode((window.width, window.height), flags=pygame.SCALED)  # , vsync=1)

        from .config import Config  # imported here to avoid circular import

        self.config = GameConfig(
            screen=screen,
            clock=pygame.time.Clock(),
            fps=Config.fps_cap,
            window=window,
            images=Images(),
            sounds=Sounds(),
            debug=Config.debug
        )

        if Config.options['mute']:
            self.set_mute(True)

        self.gsm = GameStateManager()
        self.background = None
        self.floor = None
        self.player = None
        self.pipes = None
        self.score = None
        self.welcome_message = None
        self.game_over_message = None
        self.inventory = None
        self.item_manager = None
        self.enemy_manager = None

        self.next_closest_pipe_pair = None

    def set_mute(self, mute: bool = False):
        if mute:
            self.config.sounds = Sounds(num_channels=0)
            self.config.sounds.set_muted(True)
        else:
            self.config.sounds = Sounds(num_channels=50)
            self.config.sounds.set_muted(False)

    async def start(self):
        while True:
            self.reset()
            # await self.start_screen()
            await self.play()
            await self.game_over()

    def reset(self):
        self.config.images.randomize()
        self.background = Background(self.config)
        self.floor = Floor(self.config)
        self.player = Player(self.config, self.gsm)
        self.welcome_message = WelcomeMessage(self.config)
        self.game_over_message = GameOver(self.config)
        self.pipes = Pipes(self.config)
        self.score = Score(self.config)
        self.inventory = Inventory(self.config, self.player)
        self.item_manager = ItemManager(self.config, self.inventory, self.pipes)
        self.enemy_manager = EnemyManager(self.config)
        self.next_closest_pipe_pair = (self.pipes.upper[0], self.pipes.lower[0])

    async def start_screen(self):
        self.gsm.set_state(GameState.START)
        self.player.set_mode(PlayerMode.SHM)

        while True:
            for event in pygame.event.get():
                if self.handle_events(event):
                    return

            self.background.tick()
            self.floor.tick()
            self.player.tick()
            self.welcome_message.tick()

            pygame.display.update()
            await asyncio.sleep(0)
            self.config.tick()

    async def play(self):
        self.gsm.set_state(GameState.PLAY)
        self.player.set_mode(PlayerMode.NORMAL)
        self.score.reset()

        count = 0

        while True:
            print("START")
            self.monitor_fps_drops(fps_threshold=27)
            if self.player.crossed(self.next_closest_pipe_pair[0]):
                self.next_closest_pipe_pair = self.get_next_pipe_pair()
                self.score.add()

            # self.player.handle_bad_collisions(self.pipes, self.floor)
            # if self.is_player_dead():
            #     return

            collided_items = self.player.collided_items(self.item_manager.spawned_items)  # collided with a spawned item(s)
            self.item_manager.collect_items(collided_items)
            self.update_bullet_info()

            for event in pygame.event.get():
                if self.handle_events(event):
                    return
            self.handle_held_buttons()

            if count % 19 == 0:
                self.player.flap()
            count += 1

            self.game_tick()

            pygame.display.update()
            await asyncio.sleep(0)
            self.config.tick()

            inventory_slot = self.inventory.inventory_slots[0]
            if inventory_slot.item.name != ItemName.EMPTY and inventory_slot.item.shot_bullets:
                print([(b.x, b.y) for b in inventory_slot.item.shot_bullets])
            print("END")
            print()

    async def game_over(self):
        self.gsm.set_state(GameState.END)
        self.player.set_mode(PlayerMode.CRASH)

        self.pipes.stop()
        self.floor.stop()
        self.item_manager.stop()
        self.enemy_manager.stop()
        self.inventory.stop()

        while True:
            for event in pygame.event.get():
                if self.handle_events(event):
                    return

            self.game_tick()
            self.game_over_message.tick()

            pygame.display.update()
            await asyncio.sleep(0)
            self.config.tick()

    def game_tick(self):
        self.background.tick()
        self.pipes.tick()
        self.floor.tick()
        self.item_manager.tick()
        self.player.tick()
        self.enemy_manager.tick()
        self.inventory.tick()
        self.score.tick()

    @staticmethod
    def get_pipe_pair_center(pipe_pair) -> (float, float):
        upper = pipe_pair[0]
        lower = pipe_pair[1]
        vertical_center = (upper.y + upper.h + lower.y) / 2
        return upper.cx, vertical_center

    def get_next_pipe_pair(self):
        return (
            self.pipes.upper[self.pipes.upper.index(self.next_closest_pipe_pair[0]) + 1],
            self.pipes.lower[self.pipes.lower.index(self.next_closest_pipe_pair[1]) + 1]
        )

    def is_player_dead(self) -> bool:
        if self.player.hp_manager.current_value <= 0:
            if self.player.invincibility_frames > 0:
                return False
            elif self.inventory.inventory_slots[5].item.quantity > 0:
                self.inventory.use_item(5)
                return False
            elif self.player.invincibility_frames <= 0:
                return True
        return False

    def update_bullet_info(self):
        # TODO Any idea how to optimize passing info to bullets?
        spawned_enemies = set()
        current_bullets = set()
        inventory_slot = self.inventory.inventory_slots[0]

        # player bullets
        if inventory_slot.item.name != ItemName.EMPTY and inventory_slot.item.shot_bullets:
            current_bullets.update(inventory_slot.item.shot_bullets)

        # enemy bullets
        for group in self.enemy_manager.spawned_enemy_groups:
            spawned_enemies.update(group.members)
            for enemy in group.members:
                current_bullets.update(enemy.gun.shot_bullets)

        pipes = self.pipes.upper + self.pipes.lower
        for bullet in current_bullets:
            bullet.set_entities(self.player, list(spawned_enemies), pipes)

    def handle_events(self, event) -> bool:
        self.handle_quit(event)

        if self.player.mode == PlayerMode.SHM:
            if event.type == KEYDOWN and event.key == K_SPACE:
                return True

        elif self.player.mode == PlayerMode.CRASH:
            if event.type == KEYDOWN and event.key == K_SPACE:
                if self.player.y + self.player.h >= self.floor.y - 1:  # waits for bird crash animation to end
                    return True

        elif self.player.mode == PlayerMode.NORMAL:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    self.player.flap()
                elif event.key == pygame.K_a:
                    self.inventory.use_item(inventory_slot_index=2)
                elif event.key == pygame.K_s:
                    self.inventory.use_item(inventory_slot_index=3)
                elif event.key == pygame.K_d:
                    self.inventory.use_item(inventory_slot_index=4)
                elif event.key == pygame.K_r:
                    self.inventory.use_item(inventory_slot_index=1)  # ammo slot
            return False

    @staticmethod
    def handle_quit(event):
        if event.type == QUIT:
            print("Quitting...")
            pygame.quit()
            sys.exit()

    def handle_held_buttons(self):
        m_left, _, _ = pygame.mouse.get_pressed()
        m_left = True # TODO remove
        if m_left:
            self.inventory.use_item(inventory_slot_index=0)  # gun slot

    def monitor_fps_drops(self, fps_threshold):
        curr_fps = self.config.clock.get_fps()
        if curr_fps < fps_threshold:
            print("FPS drop:", curr_fps)
