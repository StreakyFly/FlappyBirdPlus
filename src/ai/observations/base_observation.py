class BaseObservation:
    def __init__(self, env, **kwargs):
        self.env = env  # game environment

    def get_observation(self, *args):
        raise NotImplementedError("get_observation() method should be implemented in a subclass.")
