import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.pyengine2D.core.engine import Engine
from src.pyengine2D.core.input import Keys

def test_input_enhancement():
    # Setup dummy engine
    engine = Engine("Test Input", 100, 100)
    inp = engine.input

    # Inject mock input state
    inp._keys[Keys.SPACE] = True
    inp._prev_keys[Keys.SPACE] = False
    
    inp._mouse_buttons = (True, False, False)
    inp._prev_mouse_buttons = (False, False, False)

    # 1. Test just_pressed
    assert inp.is_key_just_pressed(Keys.SPACE) is True
    assert inp.is_mouse_just_pressed(0) is True

    # 2. Test input consumption
    assert inp.is_key_pressed(Keys.SPACE) is True
    inp.consume_key(Keys.SPACE)
    assert inp.is_key_pressed(Keys.SPACE) is False
    assert inp.is_key_just_pressed(Keys.SPACE) is False

    assert inp.is_mouse_pressed(0) is True
    inp.consume_mouse(0)
    assert inp.is_mouse_pressed(0) is False
    assert inp.is_mouse_just_pressed(0) is False

    # 3. Next frame (simulated)
    inp._update() # Usually calls pygame, but since we're in headless it just clears consumed state
    
    # Inject state simulating key release
    inp._keys[Keys.SPACE] = False
    inp._prev_keys[Keys.SPACE] = True
    
    inp._mouse_buttons = (False, False, False)
    inp._prev_mouse_buttons = (True, False, False)

    # 4. Test just_released
    assert inp.is_key_just_released(Keys.SPACE) is True
    assert inp.is_mouse_just_released(0) is True

    # 5. Consume release
    inp.consume_key(Keys.SPACE)
    assert inp.is_key_just_released(Keys.SPACE) is False

if __name__ == "__main__":
    test_input_enhancement()
    print("[PASS] test_input_enhancement")
