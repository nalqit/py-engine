import pygame


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

    # ---- Surface management ----

    def create_surface(self, w, h, alpha=False):
        if alpha:
            return pygame.Surface((int(w), int(h)), pygame.SRCALPHA)
        return pygame.Surface((int(w), int(h)))

    def fill(self, surface, color):
        surface.fill(color)

    def blit(self, dest, src, pos, blend_mode=None):
        if blend_mode is not None:
            dest.blit(src, pos, special_flags=blend_mode)
        else:
            dest.blit(src, pos)

    def scale_surface(self, surface, w, h):
        return pygame.transform.scale(surface, (int(w), int(h)))

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

    def render_text(self, text, color, size=16, bold=False):
        """Returns a surface with the rendered text. Results are cached."""
        key = (text, color, size, bold)
        if key in self._text_cache:
            return self._text_cache[key]
        font = self._get_font(size, bold)
        surf = font.render(text, True, color)
        self._text_cache[key] = surf
        return surf

    def render_text_uncached(self, text, color, size=16, bold=False):
        """Returns a surface with the rendered text. NOT cached (for dynamic text)."""
        font = self._get_font(size, bold)
        return font.render(text, True, color)
