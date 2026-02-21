import pygame


class PixelGrid:
    """
    Engine-level pixel manipulation for cellular automata / per-pixel rendering.
    Wraps pygame.PixelArray so game code never touches it.
    """

    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.surface = pygame.Surface((width, height)).convert_alpha()
        self.surface.fill((0, 0, 0, 0))
        self._color_map = {}

    def register_color(self, key, rgba):
        """Register a material key -> RGBA color mapping."""
        self._color_map[key] = self.surface.map_rgb(rgba)

    def batch_update(self, grid_data):
        """Update entire pixel grid from a flat list. grid_data[y*width+x] = color_key."""
        cm = self._color_map
        w = self.width
        h = self.height
        with pygame.PixelArray(self.surface) as px:
            for y in range(h):
                row = y * w
                for x in range(w):
                    px[x, y] = cm[grid_data[row + x]]

    def get_surface(self):
        return self.surface
