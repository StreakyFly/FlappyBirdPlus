class BaseObservation:
    def __init__(self, entity, env, **kwargs):
        self.entity = entity  # controlled entity (e.g. player, enemy)
        self.env = env  # game environment

    def get_observation(self, *args):
        raise NotImplementedError("get_observation() method should be implemented in a subclass.")
