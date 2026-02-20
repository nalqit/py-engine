from typing import List, Optional

class Node:
    """
    Represents a node in the scene graph hierarchy.
    Handles parent-child relationships and recursive updates.
    """
    def __init__(self, name: str = "Node"):
        self.name = name
        self.parent: Optional['Node'] = None
        self.children: List['Node'] = []

    def add_child(self, child: 'Node') -> None:
        """Adds a child node to this node."""
        if child.parent:
            child.parent.remove_child(child)
        child.parent = self
        self.children.append(child)

    def remove_child(self, child: 'Node') -> None:
        """Removes a child node from this node."""
        if child in self.children:
            self.children.remove(child)
            child.parent = None
    def update_transforms(self) -> None:
        """
        Updates transforms for this node and all of its children.
        Base Node doesn't have transform data, but propagates to children.
        """
        for child in self.children:
            child.update_transforms()

    def update(self, delta: float) -> None:
        """
        Updates this node and all of its children.
        Can be overridden by subclasses to add specific behavior.
        """
        # Update children
        for child in self.children:
            child.update(delta)

    def render(self, surface) -> None:
        """
        Renders this node and its children.
        """
        for child in self.children:
            child.render(surface)
    
    def __repr__(self):
        return f"Node({self.name})"
    def get_node(self, name: str):
        if self.name == name:
            return self

        for child in self.children:
            found = child.get_node(name)
            if found:
                return found
        return None
    

    def print_tree(self, indent=0):
        prefix = " " * indent + "- "

        info = f"{self.name} ({self.__class__.__name__})"

        # Debug Collision Info إن وجد
        if hasattr(self, "layer"):
            info += f" | layer={self.layer}"

        if hasattr(self, "mask"):
            info += f" | mask={self.mask}"

        print(prefix + info)

        for child in self.children:
            child.print_tree(indent + 4)


