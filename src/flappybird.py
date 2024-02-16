import asyncio
import sys

import pygame
from pygame.locals import K_SPACE, KEYDOWN, QUIT

from .utils import GameConfig, GameState, GameStateManager, Window, Images, Sounds
from .entities import Background, Floor, Player, PlayerMode, Pipes, Score, WelcomeMessage, GameOver, \
    Inventory, ItemManager, ItemName, EnemyManager


class FlappyBird:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Flappy Bird by @StreakyFly")
        window = Window(width=720, height=960)
        screen = pygame.display.set_mode((window.width, window.height), flags=pygame.SCALED)
        self.images = Images()

        self.config = GameConfig(
            screen=screen,
            clock=pygame.time.Clock(),
            fps=30,
            window=window,
            images=self.images,
            sounds=Sounds(),
        )
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

    async def start(self):
        while True:
            self.images.randomize()
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
            await self.start_screen()
            await self.play()
            await self.game_over()

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

        while True:
            self.monitor_fps_drops(fps_threshold=28)
            self.player.handle_bad_collisions(self.pipes, self.floor)
            if self.player.hp_manager.current_value <= 0:
                if self.player.invincibility_frames > 0:
                    pass
                elif self.inventory.inventory_slots[5].item.quantity > 0:
                    self.inventory.use_item(5)
                elif self.player.invincibility_frames <= 0:
                    return

            for i, pipe in enumerate(self.pipes.upper):
                if self.player.crossed(pipe):
                    self.score.add()
            collided_items = self.player.collided_items(self.item_manager.spawned_items)  # collided with a spawned item(s)
            self.item_manager.collect_items(collided_items)

            # TODO do this for all bullets, even those from enemy guns, not just bullets from inventory gun!
            if self.inventory.inventory_slots[0].item.name != ItemName.EMPTY and self.inventory.inventory_slots[0].item.shot_bullets:
                for bullet in self.inventory.inventory_slots[0].item.shot_bullets:
                    bullet.set_entities(self.player, self.enemy_manager.spawned_enemies, self.pipes)

            for event in pygame.event.get():
                if self.handle_events(event):
                    return
            self.handle_held_buttons()

            self.background.tick()
            self.pipes.tick()
            self.floor.tick()
            self.item_manager.tick()
            self.player.tick()
            self.enemy_manager.tick()
            self.inventory.tick()
            self.score.tick()

            pygame.display.update()
            await asyncio.sleep(0)
            self.config.tick()

    async def game_over(self):
        self.gsm.set_state(GameState.END)
        self.player.set_mode(PlayerMode.CRASH)
        self.pipes.stop()
        self.floor.stop()
        self.item_manager.stop()

        while True:
            for event in pygame.event.get():
                if self.handle_events(event):
                    return

            self.background.tick()
            self.pipes.tick()
            self.floor.tick()
            self.item_manager.tick()
            self.player.tick()
            self.enemy_manager.tick()
            self.inventory.tick()
            self.score.tick()
            self.game_over_message.tick()

            self.config.tick()
            pygame.display.update()
            await asyncio.sleep(0)

    def check_quit_event(self, event):
        if event.type == QUIT:
            pygame.quit()
            sys.exit()

    def handle_events(self, event) -> bool:
        self.check_quit_event(event)

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

    def handle_held_buttons(self):
        m_left, _, _ = pygame.mouse.get_pressed()
        if m_left:
            self.inventory.use_item(inventory_slot_index=0)  # gun slot

    def monitor_fps_drops(self, fps_threshold):
        curr_fps = self.config.clock.get_fps()
        if curr_fps < fps_threshold:
            print("FPS drop:", curr_fps)
