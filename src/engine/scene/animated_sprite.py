import pygame
from .node2d import Node2D

class AnimatedSprite(Node2D):
    """
    A 2D node that renders an animation from a sprite sheet.
    """
    def __init__(self, name, sprite_sheet_path, frame_width, frame_height):
        super().__init__(name, 0, 0)
        self.sprite_sheet = pygame.image.load(sprite_sheet_path).convert_alpha()
        self.frame_width = frame_width
        self.frame_height = frame_height
        
        self.animations = {} # name -> list of frame indices
        self.current_animation = None
        self.current_frame_index = 0
        self.frame_timer = 0.0
        self.fps = 10.0
        self.loop = True
        self.playing = False
        
        # Calculate how many frames are in the sheet
        self.sheet_width, self.sheet_height = self.sprite_sheet.get_size()
        self.cols = self.sheet_width // frame_width
        self.rows = self.sheet_height // frame_height

    def add_animation(self, name, frames):
        """frames: list of (col, row) or list of index."""
        self.animations[name] = frames

    def play(self, name, fps=10, loop=True):
        if self.current_animation == name and self.playing:
            return
            
        self.current_animation = name
        self.fps = fps
        self.loop = loop
        self.current_frame_index = 0
        self.frame_timer = 0.0
        self.playing = True

    def stop(self):
        self.playing = False

    def update(self, delta: float):
        if not self.playing or not self.current_animation:
            super().update(delta)
            return

        self.frame_timer += delta
        if self.frame_timer >= 1.0 / self.fps:
            self.frame_timer = 0.0
            self.current_frame_index += 1
            
            frames = self.animations[self.current_animation]
            if self.current_frame_index >= len(frames):
                if self.loop:
                    self.current_frame_index = 0
                else:
                    self.current_frame_index = len(frames) - 1
                    self.playing = False

        super().update(delta)

    def render(self, surface: pygame.Surface):
        if not self.current_animation:
            super().render(surface)
            return

        frames = self.animations[self.current_animation]
        frame_idx = frames[self.current_frame_index]
        
        # Calculate source rect on sprite sheet
        if isinstance(frame_idx, tuple):
            col, row = frame_idx
        else:
            col = frame_idx % self.cols
            row = frame_idx // self.cols
            
        src_rect = pygame.Rect(
            col * self.frame_width,
            row * self.frame_height,
            self.frame_width,
            self.frame_height
        )
        
        sx, sy = self.get_screen_position()
        dest_pos = (int(sx), int(sy))
        
        surface.blit(self.sprite_sheet, dest_pos, src_rect)
        
        super().render(surface)
