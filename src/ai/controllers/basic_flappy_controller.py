from src.entities.player import Player
from .base_controller import BaseModelController
from ..environments import EnvType


class BasicFlappyModelController(BaseModelController):
    def __init__(self):
        super().__init__(env_type=EnvType.BASIC_FLAPPY, model_name='basic_flappy')

    @staticmethod
    def perform_action(action, entity: Player, env=None):
        if action == 1:
            entity.flap()
