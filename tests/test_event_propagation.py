import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.pyengine2D.ui.ui_node import UINode
from src.pyengine2D.ui.event_system import EventPropagationSystem, UIEvent, UIMouseEvent
from src.pyengine2D.core.engine import Engine
from src.pyengine2D.scene.node2d import Node2D


class MockEngine:
    class MockInput:
        def __init__(self):
            self.mx = 0
            self.my = 0
            self.just_pressed = False
            self.just_released = False
            self.consumed = False

        def get_mouse_pos(self):
            return self.mx, self.my

        def is_mouse_just_pressed(self, btn):
            return self.just_pressed

        def is_mouse_just_released(self, btn):
            return self.just_released

        def consume_mouse(self, btn):
            self.consumed = True

    def __init__(self):
        self.input = self.MockInput()


class TestWidget(UINode):
    def __init__(self, name, w, h):
        super().__init__(name, w, h)
        self.log = []

    def on_mouse_enter(self):
        self.log.append("enter")

    def on_mouse_exit(self):
        self.log.append("exit")

    def on_mouse_down(self, event):
        self.log.append("down")

    def on_mouse_up(self, event):
        self.log.append("up")

    def on_click(self, event):
        self.log.append("click")
        if self.name == "ChildWidget":
            event.consume()


def test_event_propagation():
    engine = MockEngine()
    eps = EventPropagationSystem(engine)
    inp = engine.input

    # Simple Hierarchy
    # Root (0,0 500x500) -> ParentWidget (10,10 200x200) -> ChildWidget (10,10 50x50) (Absolute: 20,20 to 70,70)
    root = Node2D("Root")
    
    parent = TestWidget("ParentWidget", 200, 200)
    parent.local_x = 10
    parent.local_y = 10
    
    child = TestWidget("ChildWidget", 50, 50)
    child.local_x = 10
    child.local_y = 10
    
    root.add_child(parent)
    parent.add_child(child)
    root.update_transforms()

    # 1. Test Hover (Enter / Exit)
    inp.mx, inp.my = 0, 0
    eps.process_events(root)
    assert eps._hovered_node is None

    inp.mx, inp.my = 30, 30 # Inside child
    eps.process_events(root)
    assert eps._hovered_node == child
    assert child.log == ["enter"]
    assert parent.log == [] # Parent doesn't get enter if child handles it. Wait, does parent get enter? 
    # Current implementation only tracks ONE hovered node (the deepest). 
    # It doesn't bubble enter/exit events. That is usually fine for most UI systems.

    # Move to parent only (outside child)
    inp.mx, inp.my = 100, 100
    eps.process_events(root)
    assert eps._hovered_node == parent
    assert child.log == ["enter", "exit"]
    assert parent.log == ["enter"]

    # Move outside everything
    inp.mx, inp.my = 1000, 1000
    eps.process_events(root)
    assert eps._hovered_node is None
    assert parent.log == ["enter", "exit"]

    # 2. Test Bubbling and Consumption (Click)
    parent.log.clear()
    child.log.clear()

    # Press down on child
    inp.mx, inp.my = 30, 30
    inp.just_pressed = True
    eps.process_events(root)
    
    # Child was hit. Does it bubble? Let's check.
    # Child's on_mouse_down is called, but DOES NOT CONSUME. So parent gets it too.
    assert child.log == ["enter", "down"]
    assert parent.log == ["down"]
    assert inp.consumed == False # Since nobody consumed the event

    # Release on child
    inp.just_pressed = False
    inp.just_released = True
    eps.process_events(root)

    # Child's click DOES consume!
    assert child.log == ["enter", "down", "up", "click"]
    # Parent should get UP (child did not consume UP), but NOT get CLICK (child consumed CLICK)
    assert parent.log == ["down", "up"]
    assert inp.consumed == True # The click was consumed, engine input was blocked

if __name__ == "__main__":
    test_event_propagation()
    print("[PASS] test_event_propagation")
