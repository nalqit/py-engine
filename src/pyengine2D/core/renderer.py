import pygame
from typing import Optional


class BlendMode:
    """Engine blend mode constants."""
    ADD = pygame.BLEND_RGB_ADD
    MULT = pygame.BLEND_RGB_MULT
    RGBA_MULT = pygame.BLEND_RGBA_MULT


class Renderer:
    """Engine rendering abstraction. All drawing, text, and surface ops go through here."""

    def __init__(self):
        self._font_cache = {}
        self._text_cache = {}
        self.MAX_TEXT_CACHE = 256

    # ---- Surface management ----

    def create_surface(self, w, h, alpha=False):
        if alpha:
            return pygame.Surface((int(w), int(h)), pygame.SRCALPHA)
        return pygame.Surface((int(w), int(h)))

    def fill(self, surface, color):
        surface.fill(color)

    def blit(self, dest, src, pos, area=None, blend_mode=None):
        if blend_mode is not None:
            dest.blit(src, pos, area=area, special_flags=blend_mode)
        else:
            dest.blit(src, pos, area=area)

    def scale_surface(self, surface, w, h):
        return pygame.transform.scale(surface, (int(w), int(h)))

    def flip_surface(self, surface, flip_x=False, flip_y=False):
        return pygame.transform.flip(surface, flip_x, flip_y)

    def subsurface(self, surface, rect_tuple):
        """Extract a sub-region from *surface*. rect_tuple = (x, y, w, h)."""
        return surface.subsurface(pygame.Rect(*rect_tuple))

    def scale_blit(self, dest, src, pos, src_area=None, dest_size=None,
                   flip_x=False, flip_y=False):
        """
        Extract *src_area* from *src*, scale to *dest_size*, optionally flip,
        then blit to *dest* at *pos*.  All pygame ops stay in the Renderer.
        """
        if src_area is not None:
            region = src.subsurface(pygame.Rect(*src_area))
        else:
            region = src

        if dest_size is not None:
            region = pygame.transform.scale(region, (int(dest_size[0]), int(dest_size[1])))

        if flip_x or flip_y:
            region = pygame.transform.flip(region, flip_x, flip_y)

        dest.blit(region, pos)

    def load_image(self, path, alpha=True):
        """Load an image file and return a surface (convert_alpha or convert)."""
        img = pygame.image.load(path)
        return img.convert_alpha() if alpha else img.convert()

    def get_surface_size(self, surface):
        return surface.get_size()

    def get_clip(self, surface) -> Optional[tuple]:
        """Returns the current clip rect (x, y, w, h) or None if not set."""
        rect = surface.get_clip()
        if rect.width == 0 or rect.height == 0:
            return None # Pygame returns 0-sized rect if not set/full surface
        return (rect.x, rect.y, rect.width, rect.height)

    def set_clip(self, surface, x, y, w, h):
        """Sets the clipping rectangle for all subsequent drawing on this surface."""
        surface.set_clip((int(x), int(y), int(w), int(h)))

    def clear_clip(self, surface):
        """Removes the clipping rectangle."""
        surface.set_clip(None)

    # ---- Primitives ----

    def draw_rect(self, surface, color, x, y, w, h, width=0):
        pygame.draw.rect(surface, color, (int(x), int(y), int(w), int(h)), width)

    def draw_circle(self, surface, color, cx, cy, radius, width=0):
        pygame.draw.circle(surface, color, (int(cx), int(cy)), int(radius), width)

    def draw_line(self, surface, color, x1, y1, x2, y2, width=1):
        pygame.draw.line(surface, color, (x1, y1), (x2, y2), width)

    def draw_polygon(self, surface, color, points):
        if len(points) >= 3:
            pygame.draw.polygon(surface, color, points)

    # ---- Text ----

    def _get_font(self, size, bold=False):
        key = (size, bold)
        if key not in self._font_cache:
            self._font_cache[key] = pygame.font.SysFont("Arial", size, bold=bold)
        return self._font_cache[key]

    def draw_text(self, surface, text, color, x, y, size=16, bold=False):
        """Convenience method to render and blit text using the cache in one call."""
        surf = self.render_text(text, color, size, bold)
        self.blit(surface, surf, (int(x), int(y)))

    def render_text(self, text, color, size=16, bold=False):
        """Returns a surface with the rendered text. Results are cached."""
        key = (text, color, size, bold)
        if key in self._text_cache:
            return self._text_cache[key]
        if len(self._text_cache) >= self.MAX_TEXT_CACHE:
            # Evict oldest entry
            oldest = next(iter(self._text_cache))
            del self._text_cache[oldest]
        font = self._get_font(size, bold)
        surf = font.render(text, True, color)
        self._text_cache[key] = surf
        return surf

    def render_text_uncached(self, text, color, size=16, bold=False):
        """Returns a surface with the rendered text. NOT cached (for dynamic text)."""
        font = self._get_font(size, bold)
        return font.render(text, True, color)
