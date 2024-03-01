import asyncio
import os
import sys
import numpy as np

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
        if os.environ.get('SDL_VIDEODRIVER') == 'dummy':
            screen = pygame.display.set_mode((window.width, window.height))
        else:
            screen = pygame.display.set_mode((window.width, window.height), flags=pygame.SCALED)

        self.config = GameConfig(
            screen=screen,
            clock=pygame.time.Clock(),
            fps=900,  # default = 30
            window=window,
            images=Images(),
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

    def reset_sounds(self, mute: bool = False):
        if mute:
            self.config.sounds = Sounds(num_channels=0)
            self.config.sounds.set_muted(True)
        else:
            self.config.sounds = Sounds(num_channels=50)
            self.config.sounds.set_muted(False)

    async def start(self):
        while True:
            self.reset()
            await self.start_screen()
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
            self.get_state()
            self.monitor_fps_drops(fps_threshold=27)
            for i, pipe in enumerate(self.pipes.upper):
                if self.player.crossed(pipe):
                    self.score.add()

            self.player.handle_bad_collisions(self.pipes, self.floor)
            if self.is_player_dead():
                return

            collided_items = self.player.collided_items(
                self.item_manager.spawned_items)  # collided with a spawned item(s)
            self.item_manager.collect_items(collided_items)
            self.update_bullet_info()

            for event in pygame.event.get():
                if self.handle_events(event):
                    return

            self.handle_held_buttons()
            self.game_tick()

            pygame.display.update()
            await asyncio.sleep(0)
            self.config.tick()

    def init_env(self):
        """
        Initialize the game environment.
        :return: nothing
        """
        self.reset()
        self.reset_sounds(True)
        self.gsm.set_state(GameState.PLAY)
        self.player.set_mode(PlayerMode.NORMAL)

    def reset_env(self):
        """
        Reset the game environment.
        :return: nothing
        """
        self.reset()
        self.gsm.set_state(GameState.PLAY)
        self.player.set_mode(PlayerMode.NORMAL)

    def step(self, action):
        """
        Step through the game one frame at a time with the given action.
        :param action: an action the AI took
        :return: TODO game state
        """
        # self.monitor_fps_drops(fps_threshold=70)

        if action == 1:
            self.player.flap()

        terminated = False
        passed_pipe = False
        for i, pipe in enumerate(self.pipes.upper):
            if self.player.crossed(pipe):
                passed_pipe = True
                self.score.add()

        self.player.handle_bad_collisions(self.pipes, self.floor)
        if self.is_player_dead():
            terminated = True

        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                sys.exit()

        self.background.tick()
        self.pipes.tick()
        self.floor.tick()
        self.player.tick()
        self.score.tick()

        pygame.display.update()
        self.config.tick()

        # return observation, reward, done, truncated_something_a_bool, info
        return self.get_state(), \
            self.calculate_reward(action=action, died=terminated, passed_pipe=passed_pipe), \
            terminated, \
            False

    def get_state(self):
        """
        Get the current state of the game.
        :return: game state
        """
        player_y = self.player.y
        player_rotation = self.player.rotation
        pipe_center_positions = []
        for i, (upper, lower) in enumerate(zip(self.pipes.upper, self.pipes.lower)):
            pipe_center = (upper.cx, (upper.y + upper.h + lower.y) / 2)
            pipe_center_positions.extend(pipe_center)

        game_state = np.array([player_y, player_rotation] + pipe_center_positions, dtype=np.float32)
        return game_state

    def calculate_reward(self, action, died, passed_pipe) -> int:
        reward = 0
        if died:
            reward = -100
        elif passed_pipe:
            reward = 100
        elif action == 1:
            reward = -1

        next_pipe_y = 0
        for i, (upper, lower) in enumerate(zip(self.pipes.upper, self.pipes.lower)):
            pipe_center = (upper.cx, (upper.y + upper.h + lower.y) / 2)
            if self.player.x < pipe_center[0]:
                next_pipe_y = pipe_center[1]
                break

        vertical_distance_to_next_pipe_center = abs(self.player.y - next_pipe_y)
        if vertical_distance_to_next_pipe_center < 100:
            reward += 3

        return reward

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
        spawned_enemies = []
        for group in self.enemy_manager.spawned_enemy_groups:
            spawned_enemies.extend(group.members)

        current_bullets = []
        # TODO add all existing bullets to current_bullets, even those from enemy guns!
        if self.inventory.inventory_slots[0].item.name != ItemName.EMPTY and self.inventory.inventory_slots[
            0].item.shot_bullets:
            current_bullets.extend(self.inventory.inventory_slots[0].item.shot_bullets)
        if self.enemy_manager.spawned_enemy_groups:
            for group in self.enemy_manager.spawned_enemy_groups:
                for enemy in group.members:
                    if enemy.gun.shot_bullets:
                        current_bullets.extend(enemy.gun.shot_bullets)

        for bullet in current_bullets:
            bullet.set_entities(self.player, spawned_enemies, (self.pipes.upper + self.pipes.lower))

    def handle_events(self, event) -> bool:
        if event.type == QUIT:
            pygame.quit()
            sys.exit()

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
