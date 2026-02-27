import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.pyengine2D.core.signal import Signal
from src.pyengine2D.scene.node import Node

def test_signal_basic():
    """Test connect, emit, and disconnect on a standalone Signal."""
    sig = Signal("test_event")
    events = []
    
    def on_event(payload):
        events.append(payload)
        
    sig.connect(on_event)
    assert sig.listener_count == 1
    
    sig.emit("hello")
    assert events == ["hello"]
    
    sig.disconnect(on_event)
    assert sig.listener_count == 0

def test_signal_multiple_listeners():
    sig = Signal("multi")
    results = []
    sig.connect(lambda x: results.append(f"A:{x}"))
    sig.connect(lambda x: results.append(f"B:{x}"))
    sig.emit(10)
    assert results == ["A:10", "B:10"]

def test_signal_disconnect_during_emit():
    sig = Signal("mutating")
    results = []
    def on_event_a():
        results.append("A")
        sig.disconnect(on_event_a)
    def on_event_b():
        results.append("B")
    sig.connect(on_event_a)
    sig.connect(on_event_b)
    sig.emit()
    assert results == ["A", "B"]
    sig.emit()
    assert results == ["A", "B", "B"]

def test_node_signal_integration():
    class HealthNode(Node):
        def __init__(self):
            super().__init__("HealthNode")
            self.register_signal("on_damage")
            self.health = 100
        def take_damage(self, amount):
            self.health -= amount
            self.emit_signal("on_damage", amount)

    node = HealthNode()
    damage_taken = []
    node.get_signal("on_damage").connect(lambda amt: damage_taken.append(amt))
    node.take_damage(20)
    assert damage_taken == [20]

def test_node_destroy_signal_cleanup():
    parent = Node("Parent")
    child = Node("Child")
    parent.add_child(child)
    child.register_signal("test")
    sig = child.get_signal("test")
    called = []
    sig.connect(lambda: called.append(True))
    child.emit_signal("test")
    assert called == [True]
    child.destroy()
    assert child not in parent.children
    assert sig.listener_count == 0
    child.emit_signal("test")
    assert called == [True]

if __name__ == "__main__":
    test_signal_basic()
    test_signal_multiple_listeners()
    test_signal_disconnect_during_emit()
    test_node_signal_integration()
    test_node_destroy_signal_cleanup()
    print("[PASS] All signal tests passed")
