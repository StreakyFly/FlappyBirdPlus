import os
import sys
import threading
from datetime import datetime, timezone

import pygame

from .utils import GameConfig, GameState, GameStateManager, Window, Images, Sounds, DummySounds, ResultsManager
from .entities import MenuManager, MainMenu, Background, Floor, Player, PlayerMode, Pipes, Score, \
    WelcomeMessage, GameOver, Inventory, ItemManager, ItemName, EnemyManager, CloudSkimmer
from .ai import ObservationManager
from .database import scores_service

# from .config import Config <-- imported later to avoid circular import


class FlappyBird:
    def __init__(self):
        pygame.init()
        # pygame.display.set_caption("Flappy Bird by @StreakyFly")
        pygame.display.set_caption("Flappy Bird Plus")
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
            sounds=DummySounds() if Config.options['mute'] else Sounds(volume=Config.settings_manager.get_settings('volume')),
            settings_manager=Config.settings_manager,
            debug=Config.debug,
            save_results=Config.save_results,
        )

        self.config.sounds.play_background_music()

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
        self.menu_manager = None
        self.results_manager = ResultsManager()

        # AI stuff
        self.human_player = True
        self.observation_manager = ObservationManager()
        self.flappy_controller = None
        self.enemy_cloudskimmer_controller = None

        # Miscellaneous
        self.next_closest_pipe_pair = None

    def init_model_controllers(self, human_player: bool = True):
        """
        Initializes the model controllers for the player and the enemies.
        This method should be called outside the FlappyBird class, before the game loop starts.
        :param human_player: whether a human will control the flappy bird, or the AI
        """
        from .ai.controllers import BasicFlappyModelController, EnemyCloudSkimmerModelController
        self.human_player = human_player
        if not human_player:
            self.flappy_controller = BasicFlappyModelController()
        self.enemy_cloudskimmer_controller = EnemyCloudSkimmerModelController()

    async def start(self):
        while True:
            self.reset()
            self.start_screen()
            self.play()
            self.game_over()

    def reset(self):
        self.config.images.randomize()
        self.menu_manager = MenuManager()
        self.menu_manager.push_menu(MainMenu(self.config, self.menu_manager))
        self.background = Background(self.config)
        self.floor = Floor(self.config)
        self.player = Player(self.config, self.gsm)
        self.welcome_message = WelcomeMessage(self.config)
        self.game_over_message = GameOver(self.config)
        self.pipes = Pipes(self.config)
        self.score = Score(self.config)
        self.inventory = Inventory(self.config, self.player)
        self.item_manager = ItemManager(self.config, self.inventory, self.pipes)
        self.enemy_manager = EnemyManager(self.config, self)
        self.next_closest_pipe_pair = (self.pipes.upper[0], self.pipes.lower[0])

    def start_screen(self):
        self.gsm.set_state(GameState.START)
        self.player.set_mode(PlayerMode.SHM)

        while True:
            for event in pygame.event.get():
                self.menu_manager.handle_event(event)
                if self.handle_event(event) and self.menu_manager.current_menu == self.menu_manager.menu_stack[0]:
                    return
                if not self.menu_manager.current_menu:
                    return

            self.background.tick()
            self.floor.tick()
            self.menu_manager.tick()

            pygame.display.update()
            self.config.tick()

    def play(self):
        """
        Order of operations should be as follows:
        1. get actions for all entities based on current observation (it's similar in training environments)
        2. perform those actions for all entities
        3. update the game state
        4. update the screen

        This way entities don't have an advantage over each other, as they all get the info of the same frame.
        They also don't have an advantage over player, as entities get the info of the frame that's currently displayed
        on the screen.

        If player is a human player, we can safely handle player input after all controlled entities performed their
        actions, as the screen hasn't been updated yet, so the human player still sees the previous frame.
        However, we shouldn't handle player input before all controlled entities perform their actions, as they would
        have a 1 frame advantage over the player, as they would know what the player did in the current frame,
        even though the screen hasn't been updated yet.
        """
        self.gsm.set_state(GameState.PLAY)
        self.player.set_mode(PlayerMode.NORMAL)
        self.score.reset()

        while True:
            # print("START")
            self.monitor_fps_drops()

            self.perform_entity_actions()
            # handle events including player input
            for event in pygame.event.get():
                if self.handle_event(event):
                    return
            self.handle_mouse_buttons()

            if self.player.crossed(self.next_closest_pipe_pair[0]):
                self.next_closest_pipe_pair = self.get_next_pipe_pair()
                self.score.add()

            self.player.handle_bad_collisions(self.pipes, self.floor)
            if self.is_player_dead():
                return

            collided_items = self.player.collided_items(self.item_manager.spawned_items)
            self.item_manager.collect_items(collided_items)
            self.update_bullet_info()

            self.game_tick()

            pygame.display.update()
            self.config.tick()

            # print("END")
            # print()

    def perform_entity_actions(self):
        # CloudSkimmer's action is influenced by (advanced) flappy bird's action (position) and advanced flappy
        # bird's action is influenced by CloudSkimmer's action. Meaning if we update either of them before the other
        # one, the one updated last will have a 1 frame advantage, as it will know what the other one did - we do NOT
        # want that, as it's not fair + they weren't trained that way.
        # In all training environments we get observation data at the end of the step and then perform actions at
        # the start of the next step. So, before performing actions, the game state doesn't change. We get observation,
        # then we perform actions. We'll do basically the same thing here. First we predict actions for all agents,
        # only after that we perform those actions. This way all agents will get the info of the same frame - no agent
        # will get the info of what some other agent that was updated before him did, as actions were predicted before
        # updating any agent.
        # It's same with player actions. If player performs an action before CloudSkimmer gets observation,
        # CloudSkimmer will have 1 frame advantage. Which is not OK either.

        controlled_entities = []
        if not self.human_player:
            controlled_entities.append(self.player)
        if self.enemy_manager.spawned_enemy_groups:
            if self.enemy_manager.spawned_enemy_groups[0].members and \
                    isinstance(self.enemy_manager.spawned_enemy_groups[0].members[0], CloudSkimmer):
                controlled_entities.extend(self.enemy_manager.spawned_enemy_groups[0].members)

        # get actions for all entities
        actions = []
        for entity in controlled_entities:
            if entity not in self.observation_manager.observation_instances:
                if isinstance(entity, CloudSkimmer):
                    self.observation_manager.create_observation_instance(entity, env=self, controlled_enemy_id=entity.id)
                else:
                    self.observation_manager.create_observation_instance(entity, env=self)

            controller = self.get_corresponding_controller(entity)
            observation = self.observation_manager.get_observation(entity)
            # TODO this if statement will later need to be modified, as advanced flappy bird will use action masks
            use_action_masks = False if isinstance(entity, Player) else True
            action = controller.predict_action(observation, use_action_masks=use_action_masks, entity=entity, env=self)
            actions.append(action)

        # perform actions for all entities
        for i, entity in enumerate(controlled_entities):
            controller = self.get_corresponding_controller(entity)
            controller.perform_action(entity, actions[i])

    def get_corresponding_controller(self, entity):
        if isinstance(entity, Player):
            return self.flappy_controller
        elif isinstance(entity, CloudSkimmer):
            return self.enemy_cloudskimmer_controller
        else:
            raise ValueError(f"Unknown entity type: {type(entity)}")

    def game_over(self):
        self.gsm.set_state(GameState.END)
        self.player.set_mode(PlayerMode.CRASH)

        self.pipes.stop()
        self.floor.stop()
        self.item_manager.stop()
        self.enemy_manager.stop()
        self.inventory.stop()

        if self.score.score > 0 and self.config.save_results:
            threading.Thread(target=self.submit_result_async, daemon=True).start()

        while True:
            for event in pygame.event.get():
                if self.handle_event(event):
                    return

            self.game_tick()
            self.game_over_message.tick()

            pygame.display.update()
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
        if self.player.hp_manager.current_value > 0:
            return False
        elif self.player.invincibility_frames > 0:
            return False
        elif self.inventory.inventory_slots[5].item.quantity > 0:
            self.inventory.use_item(5)
            return False
        return True

    def update_bullet_info(self):
        # TODO Any idea how to optimize passing info to bullets?
        #  Pass reference of the game environment to the guns, which will pass it to bullets when firing? This way we
        #  don't have to pass the info to all bullets every frame, but only when they are fired.
        spawned_enemies = set()
        current_bullets = set()
        inventory_slot = self.inventory.inventory_slots[0]

        # player bullets
        if inventory_slot.item.name != ItemName.EMPTY and inventory_slot.item.shot_bullets:
            current_bullets.update(inventory_slot.item.shot_bullets)

        # enemy bullets
        for group in self.enemy_manager.spawned_enemy_groups:
            spawned_enemies.update(group.members)
            if group.members and isinstance(group.members[0], CloudSkimmer):
                for enemy in group.members:
                    current_bullets.update(enemy.gun.shot_bullets)

        pipes = self.pipes.upper + self.pipes.lower
        for bullet in current_bullets:
            bullet.set_entities(self.player, list(spawned_enemies), pipes)

    def handle_event(self, event) -> bool:
        """
        Handles the event and returns True if the mode is to be exited, False otherwise.
        :param event: the event to handle
        :return: True if the mode is to be exited, False otherwise
        """
        self.handle_quit(event)

        if self.player.mode == PlayerMode.NORMAL and self.human_player:
            if event.type == pygame.KEYDOWN:
                match event.key:
                    case pygame.K_SPACE:
                        self.player.flap()
                    case pygame.K_a:
                        self.inventory.use_item(inventory_slot_index=2)
                    case pygame.K_s:
                        self.inventory.use_item(inventory_slot_index=3)
                    case pygame.K_d:
                        self.inventory.use_item(inventory_slot_index=4)
                    case pygame.K_r:
                        self.inventory.use_item(inventory_slot_index=1)  # ammo slot
            return False

        elif self.player.mode == PlayerMode.SHM:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                return True

        elif self.player.mode == PlayerMode.CRASH:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                if self.player.y + self.player.h >= self.floor.y - 1:  # waits for bird crash animation to end
                    return True
        return False

    def handle_mouse_buttons(self):
        if not self.human_player:
            return
        m_left, _, _ = pygame.mouse.get_pressed()
        if m_left:
            self.inventory.use_item(inventory_slot_index=0)  # gun slot

    @staticmethod
    def handle_quit(event):
        if event.type == pygame.QUIT:
            print("Quitting...")
            pygame.quit()
            sys.exit()

    def submit_result_async(self):
        current_time = datetime.now(timezone.utc).isoformat()
        self.results_manager.submit_result(self.score.score, current_time)
        scores_service.submit_score(self.config.settings_manager.get_setting("username"), self.score.score)

    def monitor_fps_drops(self, fps_threshold=None):
        """
        Extremely advanced algorithm to monitor FPS drops
        written by the one and only @StreakyFly.
        """
        fps_threshold = fps_threshold or int(self.config.fps * 0.9)
        curr_fps = self.config.clock.get_fps()

        if curr_fps < fps_threshold:
            print("FPS drop:", curr_fps)
