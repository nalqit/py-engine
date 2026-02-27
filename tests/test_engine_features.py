import os
import sys
import pygame
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.pyengine2D.core.engine import Engine
from src.pyengine2D.core.renderer import Renderer
from src.pyengine2D.utils.object_pool import ObjectPool
from src.pyengine2D.scene.node2d import Node2D


def test_engine_accumulator_cap():
    """Test that the engine accumulator properly caps dt to avoid spiral-of-death."""
    engine = Engine("Test Engine", 100, 100)
    engine._last_time = engine.get_ticks_ms()
    
    # Simulate a massive lag spike (5 seconds)
    engine._last_time -= 5000 
    
    dt = engine.begin_frame()
    dt = engine.begin_frame()
    # E01 cap is set to MAX_DT = 0.1
    assert dt <= 0.1, f"Engine delta time {dt} exceeded max_dt 0.1"


def test_renderer_text_cache_bounds():
    """Test that Renderer._text_cache does not grow infinitely."""
    pygame.font.init()
    if not pygame.get_init():
        pytest.skip("Pygame failed to initialize")
    if not pygame.display.get_surface():
        pygame.display.set_mode((1, 1), pygame.NOFRAME | pygame.HIDDEN)
        
    engine = Engine("Test Render", 100, 100)
    renderer = engine.renderer
    
    # Generate more strings than the cache size (e.g. 300 > 100/256?)
    # We set MAX_TEXT_CACHE = 256 in renderer
    max_cache = renderer.MAX_TEXT_CACHE
    
    for i in range(max_cache + 50):
        # We use render_text directly so it hits the cache
        renderer.render_text(f"Test String {i}", (255, 255, 255))
        
    assert len(renderer._text_cache) <= max_cache, "Text cache exceeded maximum bounds!"


def test_object_pool_reuse():
    """Test that the ObjectPool correctly tracks and reuses objects."""
    class DummyNode(Node2D):
        _id = 0
        def __init__(self):
            DummyNode._id += 1
            super().__init__(f"Dummy_{DummyNode._id}")
            self.active = False
            
    pool = ObjectPool(lambda: DummyNode(), 5)
    
    # Get all 5 objects
    objs = [pool.acquire() for _ in range(5)]
    assert all(o is not None for o in objs), "Pool failed to create objects"
    
    # 6th should be None if we have no dynamic allocation, but wait...
    # The pool implementation in object_pool.py creates new if empty
    obj6 = pool.acquire()
    assert obj6 is not None, "Pool should allocate on demand if exhausted"
    
    # Return 2 objects
    pool.release(objs[0])
    pool.release(objs[1])
    
    # Get 1 back, it should be one of the returned ones
    reused = pool.acquire()
    assert reused in (objs[0], objs[1]), "Pool did not reuse returned object"

