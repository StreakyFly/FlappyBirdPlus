from typing import List

import pygame


class Animation:
    def __init__(self, images, image_duration=5, loop=True):
        self.images: List[pygame.Surface] = images
        self.image_duration: int = image_duration
        self.loop: bool = loop

        self.frames_per_cycle: int = len(images) * image_duration
        self.running: bool = True
        self.frame: int = 0  # animation frame

    def copy(self):
        # if you need multiple instances of the same animation
        return Animation(self.images, self.image_duration, self.loop)

    def update(self) -> pygame.Surface:
        if not self.running:
            return self.get_image()

        if self.loop:
            self.frame = (self.frame + 1) % self.frames_per_cycle
        else:
            self.frame = min(self.frame + 1, self.frames_per_cycle - 1)
            if self.frame >= self.frames_per_cycle - 1:
                self.running = False

        return self.get_image()

    def get_image(self):
        return self.images[self.frame // self.image_duration]

    def stop(self):
        self.running = False

    def resume(self):
        self.running = True

    def restart(self):
        self.running = True
        self.frame = 0
