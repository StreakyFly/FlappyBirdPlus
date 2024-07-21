from .base_controller import BaseModelController

from src.entities.player import Player


class BasicFlappyModelController(BaseModelController):
    def __init__(self):
        super().__init__(env_type='basic_flappy', model_name='basic_flappy')

    def perform_action(self, entity: Player, action):
        if action == 1:
            entity.flap()
