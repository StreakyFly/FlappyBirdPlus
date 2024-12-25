class Pause:
    def __init__(self, paused=False):
        self.paused = paused
        self.timer = 0
        self.pauseTime = None
        self.func = None
        
    def update(self, dt):
        if self.pauseTime is not None:
            self.timer += dt
            if self.timer >= self.pauseTime:
                self.timer = 0
                self.paused = False
                self.pauseTime = None
                return self.func
        return None

    def set_pause(self, pause_time=None, func=None):
        self.timer = 0
        self.func = func
        self.pauseTime = pause_time
        self.paused = not self.paused
