from src.scene import Node

class TestNode(Node):
    """Subclass of Node to verify update calls."""
    def update(self, delta: float) -> None:
        print(f"Updating {self.name} with delta={delta}")
        super().update(delta)

def test_nodes():
    print("--- Node System Test Start ---")
    
    # Create hierarchy
    root = TestNode("Root")
    child1 = TestNode("Child1")
    child2 = TestNode("Child2")
    grandchild = TestNode("Grandchild")
    
    # Build tree
    root.add_child(child1)
    root.add_child(child2)
    child1.add_child(grandchild)
    
    # Verify structure
    print(f"Root children: {[c.name for c in root.children]}")
    print(f"Child1 children: {[c.name for c in child1.children]}")
    
    # Test Update
    print("\nCalling root.update(0.16)...")
    root.update(0.16)
    
    # Test Remove
    print("\nRemoving Child1...")
    root.remove_child(child1)
    print(f"Root children after remove: {[c.name for c in root.children]}")
    
    print("\nCalling root.update(0.16) again...")
    root.update(0.16) # Should only update Child2

    print("=== Scene Graph Tree ===")
    root.print_tree()
    print("========================")
    
    print("--- Node System Test End ---")

if __name__ == "__main__":
    test_nodes()
