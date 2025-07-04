from weakref import WeakKeyDictionary

import numpy as np

from src.entities.enemies import CloudSkimmer
from src.entities.player import Player
from .advanced_flappy_observation import AdvancedFlappyObservation
# from .basic_flappy_observation import BasicFlappyObservation
from .enemy_cloudskimmer_observation import EnemyCloudSkimmerObservation


class ObservationManager:
    # TODO When to create an observation instance?
    #  Simplest solution in flappybird.py would be when looping through the entities, before calling predict_action(),
    #  check if they're already in the observation_instances dict, otherwise create the observation instance. Each
    #  controlled entity should have its own observation class instance.

    def __init__(self):
        # maps an entity to its observation instance (allows for garbage collection)
        self.observation_instances = WeakKeyDictionary()

        # maps an entity to its observation class
        self.observation_classes = {
            # TODO [INFO]: uncomment/comment if you want to switch between `basic` and `advanced` flappy observation
            # Player: BasicFlappyObservation,  # what a genius idea it was to map by entity type (-_-')
            Player: AdvancedFlappyObservation,
            CloudSkimmer: EnemyCloudSkimmerObservation,
        }

    def create_observation_instance(self, entity, env, **kwargs) -> None:
        # TODO This name sucks, what should this method be called? Maybe create_observer()?
        """
        Creates an observation instance for the given entity.
        :param entity: the entity for which to create the observation instance
        :param env: the game environment
        :param kwargs: keyword arguments to pass to the observation class
        """
        self.observation_instances[entity] = self.observation_classes[type(entity)](entity, env, **kwargs)

    def get_observation(self, entity) -> np.ndarray | dict:
        """
        Retrieves an observation for the given agent type.
        :param entity: the entity for which to get the observation
        :return: observation for the given agent type
        """
        return self.observation_instances[entity].get_observation()
