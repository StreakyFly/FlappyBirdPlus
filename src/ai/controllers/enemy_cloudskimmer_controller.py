import numpy as np

from .base_controller import BaseModelController

from src.entities.enemies.cloudskimmer import CloudSkimmer
from src.entities.items import Gun


class EnemyCloudSkimmerModelController(BaseModelController):
    def __init__(self):
        super().__init__(env_type='enemy_cloudskimmer', model_name='enemy_cloudskimmer')

    def perform_action(self, entity: CloudSkimmer, action):
        entity.rotate_gun(action[1])

        if action[0] == 0:
            return
        elif action[0] == 1:
            entity.shoot()
        elif action[0] == 2:
            entity.reload()

    @staticmethod
    def get_action_masks(gun: Gun) -> np.ndarray:
        # initialize masks for each action type, all actions are initially available
        fire_reload_masks = np.ones(3, dtype=int)  # [do nothing, fire, reload]
        rotation_masks = np.ones(3, dtype=int)  # [do nothing, rotate up, rotate down]

        # gun can't be neither fired nor reloaded if it's on reload cooldown
        if gun.remaining_reload_cooldown > 0:
            fire_reload_masks[1] = 0  # disable fire
            fire_reload_masks[2] = 0  # disable reload

        # gun can't be fired if it's on shoot cooldown or if there's no ammo left in the gun
        if gun.remaining_shoot_cooldown > 0 or gun.quantity <= 0:
            fire_reload_masks[1] = 0  # disable fire

        # gun "can't" be reloaded if it's already full or if there's no ammo left in the inventory
        if gun.quantity == gun.magazine_size or gun.ammo_item.quantity <= 0:
            fire_reload_masks[2] = 0  # disable reload

        action_masks = np.array([fire_reload_masks, rotation_masks])
        return action_masks
