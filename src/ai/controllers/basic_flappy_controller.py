from .base_controller import BaseModelController
from ..environments import EnvType

from src.entities.player import Player


class BasicFlappyModelController(BaseModelController):
    def __init__(self):
        super().__init__(env_type=EnvType.BASIC_FLAPPY, model_name='basic_flappy')

    @staticmethod
    def perform_action(entity: Player, action):
        if action == 1:
            entity.flap()
