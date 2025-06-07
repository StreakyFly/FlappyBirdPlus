import numpy as np

from src.entities.enemies import CloudSkimmer
from src.entities.items import Gun
from .base_controller import BaseModelController
from ..environments import EnvType


class EnemyCloudSkimmerModelController(BaseModelController):
    def __init__(self):
        super().__init__(env_type=EnvType.ENEMY_CLOUDSKIMMER, model_name='enemy_cloudskimmer')

    @staticmethod
    def perform_action(action, entity: CloudSkimmer, env=None):
        entity.rotate_gun(action[1])

        if action[0] == 0:
            return
        elif action[0] == 1:
            entity.shoot()
        elif action[0] == 2:
            entity.reload()

    @staticmethod
    def get_action_masks(entity: CloudSkimmer, env) -> np.ndarray:
        gun: Gun = entity.gun

        # initialize masks for each action type, all actions are initially available
        fire_reload_masks = np.ones(3, dtype=np.int8)  # [do nothing, fire, reload]
        rotation_masks = np.ones(3, dtype=np.int8)  # [do nothing, rotate up, rotate down]

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

        # a lil cheat hehe: gun can't be fired if it's aimed at the middle enemy (when he's alive)
        # Agent has mostly learned to not shoot at the middle enemy, but in certain situations it still does.
        # TODO: if you move any of the CloudSkimmers or anything like that, this will most likely need to be adjusted.
        if fire_reload_masks[1] != 0 and any(enemy.id == 1 for enemy in env.enemy_manager.spawned_enemy_groups[0].members):
            if (entity.id == 0 and gun.rotation > 30) or (entity.id == 2 and gun.rotation < -28):
                fire_reload_masks[1] = 0

        action_masks = np.array([fire_reload_masks, rotation_masks])
        return action_masks
