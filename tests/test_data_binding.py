import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.engine.ui.data_binding import ObservableModel, DataBinding

class MockNode:
    def __init__(self):
        self.text = ""
        
    def set_text(self, t):
        self.text = t

def test_data_binding():
    model = ObservableModel()
    model.set("score", 0)
    model.set("name", "Player")
    
    # Needs a flush to emit initial changes (though DataBinding syncs immediately on creation)
    model.flush_changes()
    
    node1 = MockNode()
    node2 = MockNode()
    
    # Bind score to node1.set_text
    bind1 = DataBinding(node1, node1.set_text, model, "score", lambda s: f"Score: {s}")
    
    # Bind name to node2.set_text
    bind2 = DataBinding(node2, node2.set_text, model, "name")
    
    # 1. Verify initial sync
    assert node1.text == "Score: 0"
    assert node2.text == "Player"
    
    # 2. Update model
    model.set("score", 100)
    model.set("score", 200) # Multiple updates should coalesce
    model.set("name", "Hero")
    
    # Values shouldn't propagate automatically unfil flushed
    assert node1.text == "Score: 0"
    assert node2.text == "Player"
    
    model.flush_changes()
    
    # 3. Verify coalesced propagation
    assert node1.text == "Score: 200"
    assert node2.text == "Hero"
    
    # 4. Verify unbind
    bind1.unbind()
    model.set("score", 999)
    model.flush_changes()
    
    # Node1 shouldn't change
    assert node1.text == "Score: 200"
    
if __name__ == "__main__":
    test_data_binding()
    print("[PASS] test_data_binding")
