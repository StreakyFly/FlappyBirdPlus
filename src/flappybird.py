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

        self.next_closest_pipe_pair = None

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

        while True:
            self.monitor_fps_drops(fps_threshold=27)
            # for i, pipe in enumerate(self.pipes.upper):
            #     if self.player.crossed(pipe):
            #         self.score.add()
            if self.player.crossed(self.next_closest_pipe_pair[0]):
                self.next_closest_pipe_pair = self.get_next_pipe_pair()
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

            # self.get_state()  # TODO just a heads up that this is called here

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

    def step_basic_flappy(self, action):
        """
        Step through the game one frame at a time with the given action.
        :param action: an action the agent took - flap (1) or do nothing (0)
        :return: observation, reward, terminated, truncated
        """
        if action == 1:
            self.player.flap()

        terminated = False
        passed_pipe = False
        if self.player.crossed(self.next_closest_pipe_pair[0]):
            passed_pipe = True
            self.score.add()
            self.next_closest_pipe_pair = self.get_next_pipe_pair()

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

        reward = self.calculate_reward_basic_flappy(action=action, died=terminated, passed_pipe=passed_pipe)

        pygame.display.update()
        self.config.tick()

        return self.get_state_basic_flappy(), reward, terminated, False

    def step_enemy_cloudskimmer(self, action):
        """
        Step through the game one frame at a time with the given action.
        :param action: an action the agent took - TODO actions the agent can take
        :return: observation, reward, terminated, truncated
        """
        # TODO train a single enemy cloudskimmer for each environment - all 3 cloudskimmers needs to be present, but
        #  only one will be controlled by an agent, the other two will not be firing
        #  but make sure to change which one is the one firing during training, so it learns how to fire from all
        #  positions.

        # TODO take action - did I miss any action?
        # if action[0] == 1:
        #   cloudskimmer.fire
        # if action[1] == 1:
        #   cloudskimmer.rotate_up
        # elif action[1] == 2:
        #   cloudskimmer.rotate_down

        terminated = False

        # TODO probs remove this, score is irrelevant for enemies
        # if self.player.crossed(self.next_closest_pipe_pair[0]):
        #     self.score.add()
        #     self.next_closest_pipe_pair = self.get_next_pipe_pair()

        # TODO probs also remove this, because player hitting the pipe has "nothing" to do with the enemy agent
        # self.player.handle_bad_collisions(self.pipes, self.floor)
        # if self.is_player_dead():
        #     terminated = True

        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                sys.exit()

        self.background.tick()
        self.pipes.tick()
        self.floor.tick()
        self.player.tick()
        self.score.tick()

        reward = self.calculate_reward_enemy_cloudskimmer(action=action)

        pygame.display.update()
        self.config.tick()

        return self.get_state_enemy_cloudskimmer(), reward, terminated, False

    def step_advanced_flappy(self, action):
        """
        Step through the game one frame at a time with the given action.
        :param action: an action the agent took - TODO actions the agent can take
        :return: observation, reward, terminated, truncated
        """
        # TODO implement this function
        print("ERROR: step_advanced_flappy() is not implemented yet.")
        return False

    def get_state_basic_flappy(self):
        """
        Get the current state of the game.
        :return: game state
        """
        next_pipe_pair = next_next_pipe_pair = None
        for i, pipe in enumerate(self.pipes.upper):
            if pipe.x + pipe.w < self.player.x:
                continue

            next_pipe_pair = (pipe, self.pipes.lower[i])
            next_next_pipe_pair = (self.pipes.upper[i + 1], self.pipes.lower[i + 1])
            break

        horizontal_distance_to_next_pipe = next_pipe_pair[0].x + next_pipe_pair[0].w - self.player.x
        next_pipe_vertical_center = self.get_pipe_pair_center(next_pipe_pair)[1]
        next_next_pipe_vertical_center = self.get_pipe_pair_center(next_next_pipe_pair)[1]

        vertical_distance_to_next_pipe_center = self.player.cy - next_pipe_vertical_center
        vertical_distance_to_next_next_pipe_center = self.player.cy - next_next_pipe_vertical_center

        distances_to_pipe = [horizontal_distance_to_next_pipe,
                             vertical_distance_to_next_pipe_center,
                             vertical_distance_to_next_next_pipe_center
                             ]

        game_state = np.array([self.player.y, self.player.vel_y] + distances_to_pipe, dtype=np.float32)
        return game_state

    def get_state_enemy_cloudskimmer(self):
        """
        Get the current state of the game.
        :return: game state
        """
        # TODO modify the state, as we are missing:
        #   - current enemy position
        #   - current enemy rotation
        #   - current enemy teammates' positions
        #   - gun type
        #   - maybe even bullet locations? or maybe not...? It could learn how bullets interact just by seeing when the
        #     player gets damaged or not? although if they fire multiple bullets it will be hard to tell which bullet
        #     caused the damage

        pipe_center_positions = []
        for i, pipe_pair in enumerate(zip(self.pipes.upper, self.pipes.lower)):
            pipe_center = self.get_pipe_pair_center(pipe_pair)
            pipe_center_positions.extend(pipe_center)

        game_state = np.array([self.player.y, self.player.vel_y] + pipe_center_positions, dtype=np.float32)
        return game_state

    def get_state_advanced_flappy(self):
        """
        Get the current state of the game.
        :return: game state
        """
        # TODO implement this function
        print("WARNING! 'get_state_advanced_flappy' is not yet implemented!")
        # pipe_center_positions = []
        # for i, pipe_pair in enumerate(zip(self.pipes.upper, self.pipes.lower)):
        #     pipe_center = self.get_pipe_pair_center(pipe_pair)
        #     pipe_center_positions.extend(pipe_center)

        return False

    def get_pipe_pair_center(self, pipe_pair) -> (float, float):
        upper = pipe_pair[0]
        lower = pipe_pair[1]
        vertical_center = (upper.y + upper.h + lower.y) / 2  # TODO confirm whether this is correct
        return upper.cx, vertical_center

    def calculate_reward_basic_flappy(self, action, died, passed_pipe) -> int:
        reward = 0
        if died:
            reward -= 1000  # 400 (first 10M steps was 400, then 1000)
        else:
            reward += 1  # 2
        if passed_pipe:
            reward += 100  # 200
        if action == 1:
            reward -= 0.2  # 0.5

        for i, pipe in enumerate(self.pipes.upper):
            if pipe.x + pipe.w < self.player.x:
                continue
            else:
                pipe_center_y = self.get_pipe_pair_center((pipe, self.pipes.lower[i]))[1]
                vertical_distance_to_pipe_pair_center = abs(self.player.cy - pipe_center_y)
                # pygame.draw.circle(self.config.screen, (255, 0, 0), (pipe.cx, pipe_center_y), 5)
                # pygame.draw.line(self.config.screen, (255, 0, 0), (self.player.cx, self.player.cy), (pipe.cx, pipe_center_y), 2)
                if vertical_distance_to_pipe_pair_center < 150:
                    reward += 3  # 4
                break

        return reward

    def calculate_reward_enemy_cloudskimmer(self, action) -> int:
        reward = 0

        # TODO implement this method
        #  Agent should be rewarded for:
        #  - hitting/damaging the player (big reward)
        #  - hitting a pipe (small reward) - so the likelihood of learning a cool bounce-off-pipe strategy is higher
        #  - not firing (small reward each frame the agent doesn't fire, so if he fires but doesn't hit the player, he
        #    won't get the reward, which is like if he got punished - punishing him if bullet despawns without hitting
        #    the player might be more logical, however not only is it harder to implement, it might also confuse the
        #    agent that he was punished after one bullet's position changed to a placeholder - or if he won't know
        #    bullet positions, he would be confused why he was randomly punished a few frames after firing
        #  Agent should be punished for:
        #  - hitting himself or his teammates (big punishment)

        print("WARNING! 'calculate_reward_enemy_cloudskimmer' is not yet implemented!")

        # small reward for not firing
        # if action[0] == 0:
        #     reward += 1

        # for bullet in enemy.weapon:
        #   small reward for hitting a pipe
        #   if bullet.self.hit_entity == 'pipe':
        #       reward += 2
        #   big reward for hitting the player
        #   if bullet.self.hit_entity == 'player':
        #       reward += 300
        #   big punishment for hitting himself or his teammates
        #   if bullet.self.hit_entity == 'enemy':
        #       reward -= 100

        return reward

    def calculate_reward_advanced_flappy(self) -> int:
        reward = 0

        # TODO implement this method
        print("WARNING! 'calculate_reward_advanced_flappy' is not yet implemented!")

        return reward

    def get_next_pipe_pair(self):
        return (
            self.pipes.upper[self.pipes.upper.index(self.next_closest_pipe_pair[0]) + 1],
            self.pipes.lower[self.pipes.lower.index(self.next_closest_pipe_pair[1]) + 1]
        )

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
        # self.enemy_manager.tick()  # TODO uncomment for enemies
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
        if self.inventory.inventory_slots[0].item.name != ItemName.EMPTY and self.inventory.inventory_slots[0].item.shot_bullets:
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
