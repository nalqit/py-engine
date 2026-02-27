import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.pyengine2D.core.engine import Engine
from src.pyengine2D.scene.scene_manager import SceneManager, Scene

class MockEngine:
    pass

class TestScene(Scene):
    def __init__(self, name, log_list):
        super().__init__(name)
        self.log = log_list

    def on_enter(self):
        self.log.append(f"{self.name}:enter")

    def on_exit(self):
        self.log.append(f"{self.name}:exit")

    def on_pause(self):
        self.log.append(f"{self.name}:pause")

    def on_resume(self):
        self.log.append(f"{self.name}:resume")


def test_scene_lifecycle():
    engine = MockEngine()
    sm = SceneManager(engine)
    
    log = []
    
    scene1 = TestScene("S1", log)
    scene2 = TestScene("S2", log)
    scene3 = TestScene("S3", log)
    
    # Switch
    sm.switch_scene(scene1)
    sm.process_pending_changes() # simulates end of frame
    
    assert sm.current_scene == scene1
    assert log == ["S1:enter"]
    
    # Push S2
    sm.push_scene(scene2)
    sm.process_pending_changes()
    
    assert sm.current_scene == scene2
    # S1 should pause, S2 should enter
    assert log == ["S1:enter", "S1:pause", "S2:enter"]
    
    # Push S3
    sm.push_scene(scene3)
    sm.process_pending_changes()
    
    assert sm.current_scene == scene3
    assert log == ["S1:enter", "S1:pause", "S2:enter", "S2:pause", "S3:enter"]
    
    # Pop S3
    sm.pop_scene()
    sm.process_pending_changes()
    
    assert sm.current_scene == scene2
    # S3 should exit, S2 should resume
    assert log == ["S1:enter", "S1:pause", "S2:enter", "S2:pause", "S3:enter", "S3:exit", "S2:resume"]
    
    # Switch (should clear whole stack and push new)
    scene4 = TestScene("S4", log)
    sm.switch_scene(scene4)
    sm.process_pending_changes()
    
    assert sm.current_scene == scene4
    # S2, S1 should exit in order of stack pop. S4 enters.
    assert log[-3:] == ["S2:exit", "S1:exit", "S4:enter"]
    

if __name__ == "__main__":
    test_scene_lifecycle()
    print("[PASS] test_scene_lifecycle")
