class FontCache:
    """
    Engine Level Utility for caching rendered text surfaces.
    Reduces the cost of text rendering during heavy UI frames.
    Routes through the engine Renderer — no direct pygame usage.
    """
    _cache = {}
    _hits = 0
    _misses = 0
    
    @classmethod
    def get_text_surface(cls, text: str, color: tuple, size: int = 16, bold: bool = False):
        """Returns a cached text surface using the engine Renderer."""
        from src.pyengine2D.core.engine import Engine
        renderer = Engine.instance.renderer if Engine.instance else None
        if not renderer:
            return None

        key = (text, color, size, bold)
        if key in cls._cache:
            cls._hits += 1
            return cls._cache[key]
        cls._misses += 1
        surf = renderer.render_text(text, color, size, bold)
        cls._cache[key] = surf
        return surf
        
    @classmethod
    def get_stats(cls):
        return cls._hits, cls._misses
