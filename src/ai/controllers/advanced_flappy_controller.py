import numpy as np

from src.ai.environments import EnvType
from src.entities import Player
from src.flappybird import FlappyBird
from .base_controller import BaseModelController


class AdvancedFlappyModelController(BaseModelController):
    def __init__(self):
        super().__init__(env_type=EnvType.ADVANCED_FLAPPY, model_name='advanced_flappy')

    @staticmethod
    def perform_action(action, entity: Player, env: FlappyBird = None):
        # flap
        if action[0] == 1:
            entity.flap()

        # fire/reload
        if action[1] == 1:
            env.inventory.use_item(inventory_slot_index=0)  # gun slot
        elif action[1] == 2:
            env.inventory.use_item(inventory_slot_index=1)  # ammo slot

        # use inventory slots 2-4
        if action[2] == 1:
            env.inventory.use_item(inventory_slot_index=2)
        elif action[2] == 2:
            env.inventory.use_item(inventory_slot_index=3)
        elif action[2] == 3:
            env.inventory.use_item(inventory_slot_index=4)

    @staticmethod
    def get_action_masks(entity: Player, env: FlappyBird) -> np.ndarray:
        # TODO: implement proper action masks for Advanced Flappy Bird!
        #  - don't fire when on reload/fire cooldown or if out of ammo
        #  - don't use items when on cooldown or if out of items
        temp1 = np.ones(2, dtype=np.int8)
        temp2 = np.ones(3, dtype=np.int8)
        temp3 = np.ones(4, dtype=np.int8)

        action_masks = np.array([temp1, temp2, temp3], dtype=object)
        return action_masks
