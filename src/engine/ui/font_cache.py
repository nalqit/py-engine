import pygame

class FontCache:
    """
    Engine Level Utility for caching font surfaces.
    Reduces the cost of pygame.font.render() during heavy UI frames.
    """
    _cache = {}
    _hits = 0
    _misses = 0
    
    @classmethod
    def get_text_surface(cls, font: pygame.font.Font, text: str, color: tuple) -> pygame.Surface:
        key = (font, text, color)
        if key in cls._cache:
            cls._hits += 1
            return cls._cache[key]
        cls._misses += 1
        surf = font.render(text, True, color)
        cls._cache[key] = surf
        return surf
        
    @classmethod
    def get_stats(cls):
        return cls._hits, cls._misses
