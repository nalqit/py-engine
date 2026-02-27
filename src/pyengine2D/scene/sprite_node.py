import pygame
from .node2d import Node2D

class SpriteNode(Node2D):
    """
    A 2D node that renders a static image.
    Supports scaling, centering, and optional AssetManager integration.

    Performance features:
        - AssetManager loading (load-on-demand, shared cache).
        - Scaled surface cache (avoids repeated pygame.transform.scale per frame).
    """

    def __init__(self, name: str, image_path: str, x: float = 0.0, y: float = 0.0,
                 centered: bool = False, use_asset_manager: bool = False):
        super().__init__(name, x, y)
        self._image_path = image_path
        self.centered = centered

        if use_asset_manager:
            from src.pyengine2D.utils.asset_manager import AssetManager
            self.image = AssetManager.instance().load_image(image_path)
        else:
            self.image = pygame.image.load(image_path).convert_alpha()

        self.width, self.height = self.image.get_size()

        # Cached scaled surface
        self._scaled_cache = None      # (scale_x, scale_y) -> surface
        self._scaled_cache_key = None

    def render(self, surface: pygame.Surface):
        sx, sy = self.get_screen_position()
        
        # Apply scaling
        sw = int(self.width * self.scale_x)
        sh = int(self.height * self.scale_y)
        
        if sw <= 0 or sh <= 0:
            super().render(surface)
            return

        # Use cached scaled image when possible
        if self.scale_x != 1.0 or self.scale_y != 1.0:
            cache_key = (self.scale_x, self.scale_y)
            if cache_key != self._scaled_cache_key:
                self._scaled_cache = pygame.transform.scale(self.image, (sw, sh))
                self._scaled_cache_key = cache_key
            render_img = self._scaled_cache
        else:
            render_img = self.image

        # Adjust position if centered
        render_x, render_y = sx, sy
        if self.centered:
            render_x -= sw // 2
            render_y -= sh // 2

        surface.blit(render_img, (int(render_x), int(render_y)))
        
        super().render(surface)
