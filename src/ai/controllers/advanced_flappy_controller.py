import numpy as np

from src.ai.environments import EnvType
from src.entities import Player, ItemName
from src.entities.items import Gun
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
        # initialize masks for each action type — all actions are initially available
        flap_mask = np.ones(2, dtype=np.int8)  # [do nothing, flap]  <-- flap is always available
        gun_mask = np.ones(3, dtype=np.int8)  # [do nothing, fire, reload]
        inventory_mask = np.ones(4, dtype=np.int8)  # [do nothing, use slot 3, use slot 4, use slot 5]

        # gun_mask
        gun: Gun = env.inventory.inventory_slots[0].item
        if gun.item_name == ItemName.EMPTY:
            gun_mask[1] = 0  # disable fire
            gun_mask[2] = 0  # disable reload
        else:
            # gun can't be neither fired nor reloaded if it's on reload cooldown
            if gun.remaining_reload_cooldown > 0:
                gun_mask[1] = 0  # disable fire
                gun_mask[2] = 0  # disable reload

            # gun can't be fired if it's on shoot cooldown or if there's no ammo left in the gun
            if gun.remaining_shoot_cooldown > 0 or gun.quantity <= 0:
                gun_mask[1] = 0  # disable fire

            # gun "can't" be reloaded if it's already full or if there's no ammo left in the inventory
            if gun.quantity == gun.magazine_size or gun.ammo_item.quantity <= 0:
                gun_mask[2] = 0  # disable reload

        # inventory_mask
        inventory_slots = env.inventory.inventory_slots
        # slot is empty | entity's hunger is full
        if inventory_slots[2].item.item_name == ItemName.EMPTY or entity.food_bar.current_value >= entity.food_bar.max_value:
            inventory_mask[1] = 0
        # slot is empty | it's a shield potion but entity's shield is full | it's a health potion but entity's health is full
        if inventory_slots[3].item.item_name == ItemName.EMPTY or \
                (inventory_slots[3].item.item_name == ItemName.POTION_SHIELD and entity.shield_bar.current_value >= entity.shield_bar.max_value) or \
                (inventory_slots[3].item.item_name == ItemName.POTION_HEAL and entity.hp_bar.current_value >= entity.hp_bar.max_value):
            inventory_mask[2] = 0
        # slot is empty | entity's health is full
        if inventory_slots[4].item.item_name == ItemName.EMPTY or entity.hp_bar.current_value >= entity.hp_bar.max_value:
            inventory_mask[3] = 0

        action_masks = np.concatenate((flap_mask, gun_mask, inventory_mask), axis=0)
        return action_masks
