from typing import List

import pygame


class Animation:
    def __init__(self, frames, frame_duration=5, loop=True):
        self.frames: List[pygame.Surface] = frames
        self.frame_duration: int = frame_duration
        self.loop: bool = loop

        self.frames_per_cycle: int = len(frames) * frame_duration
        self.running: bool = True
        self.frame: int = 0  # animation frame

    def copy(self):
        # if you need multiple instances of the same animation
        return Animation(self.frames, self.frame_duration, self.loop)

    def update(self) -> pygame.Surface:
        if not self.running:
            return self.get_frame()

        if self.loop:
            self.frame = (self.frame + 1) % self.frames_per_cycle
        else:
            self.frame = min(self.frame + 1, self.frames_per_cycle - 1)
            if self.frame >= self.frames_per_cycle - 1:
                self.running = False

        return self.get_frame()

    def get_frame(self):
        return self.frames[self.frame // self.frame_duration]

    def stop(self):
        self.running = False

    def resume(self):
        self.running = True

    def reset(self):
        self.running = True
        self.frame = 0
