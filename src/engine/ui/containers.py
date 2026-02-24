from typing import List
from src.engine.ui.ui_node import UINode, SizePolicy

class BoxContainer(UINode):
    """Base for VBox and HBox. Manages spacing and child alignment."""
    def __init__(self, name: str):
        super().__init__(name, width=0, height=0)
        self.spacing = 5.0
        # By default containers wrap their content
        self.size_policy_x = SizePolicy.WRAP_CONTENT
        self.size_policy_y = SizePolicy.WRAP_CONTENT
        self.is_layout_container = True

    def get_ui_children(self) -> List[UINode]:
        return [c for c in self.children if isinstance(c, UINode)]


class VBoxContainer(BoxContainer):
    def perform_layout(self):
        super().perform_layout() # Handle base anchoring first
        
        children = self.get_ui_children()
        current_y = 0.0
        max_width = 0.0

        for child in children:
            if child.size_policy_x == SizePolicy.FILL:
                child.width = self.width - child.margin_left - child.margin_right
                
            # Position child
            child.local_x = child.margin_left
            child.local_y = current_y + child.margin_top
            child.update_transforms()

            current_y += child.height + child.margin_top + child.margin_bottom + self.spacing
            max_width = max(max_width, child.width + child.margin_left + child.margin_right)

        # Remove trailing spacing
        if children:
            current_y -= self.spacing

        # Wrap content
        if self.size_policy_x == SizePolicy.WRAP_CONTENT:
            self.width = max(self.min_width, max_width)
        if self.size_policy_y == SizePolicy.WRAP_CONTENT:
            self.height = max(self.min_height, current_y)


class HBoxContainer(BoxContainer):
    def perform_layout(self):
        super().perform_layout()
        
        children = self.get_ui_children()
        current_x = 0.0
        max_height = 0.0

        for child in children:
            if child.size_policy_y == SizePolicy.FILL:
                child.height = self.height - child.margin_top - child.margin_bottom
                
            child.local_x = current_x + child.margin_left
            child.local_y = child.margin_top
            child.update_transforms()

            current_x += child.width + child.margin_left + child.margin_right + self.spacing
            max_height = max(max_height, child.height + child.margin_top + child.margin_bottom)

        if children:
            current_x -= self.spacing

        if self.size_policy_x == SizePolicy.WRAP_CONTENT:
            self.width = max(self.min_width, current_x)
        if self.size_policy_y == SizePolicy.WRAP_CONTENT:
            self.height = max(self.min_height, max_height)


class GridContainer(BoxContainer):
    def __init__(self, name: str, columns: int = 2):
        super().__init__(name)
        self.columns = max(1, columns)

    def perform_layout(self):
        super().perform_layout()
        
        children = self.get_ui_children()
        if not children:
            if self.size_policy_x == SizePolicy.WRAP_CONTENT: self.width = self.min_width
            if self.size_policy_y == SizePolicy.WRAP_CONTENT: self.height = self.min_height
            return

        # Calculate col widths and row heights
        col_widths = [0.0] * self.columns
        row_heights = []
        
        for i, child in enumerate(children):
            col = i % self.columns
            row = i // self.columns
            
            if row >= len(row_heights):
                row_heights.append(0.0)
                
            cw = child.width + child.margin_left + child.margin_right
            ch = child.height + child.margin_top + child.margin_bottom
            
            col_widths[col] = max(col_widths[col], cw)
            row_heights[row] = max(row_heights[row], ch)

        current_y = 0.0
        for row, rh in enumerate(row_heights):
            current_x = 0.0
            for col in range(self.columns):
                idx = row * self.columns + col
                if idx >= len(children):
                    break
                
                child = children[idx]
                cw = col_widths[col]
                
                if child.size_policy_x == SizePolicy.FILL:
                    child.width = cw - child.margin_left - child.margin_right
                if child.size_policy_y == SizePolicy.FILL:
                    child.height = rh - child.margin_top - child.margin_bottom
                    
                child.local_x = current_x + child.margin_left
                child.local_y = current_y + child.margin_top
                child.update_transforms()
                
                current_x += cw + self.spacing
            
            current_y += rh + self.spacing

        if self.size_policy_x == SizePolicy.WRAP_CONTENT:
            self.width = max(self.min_width, sum(col_widths) + self.spacing * (self.columns - 1))
        if self.size_policy_y == SizePolicy.WRAP_CONTENT:
            self.height = max(self.min_height, sum(row_heights) + self.spacing * (len(row_heights) - 1))


class ScrollContainer(UINode):
    """
    A viewport that clips its children and allows scrolling.
    Must define explicit self.width and self.height.
    """
    def __init__(self, name: str, width: float, height: float):
        super().__init__(name, width, height)
        self.scroll_x = 0.0
        self.scroll_y = 0.0
        self.content_node = VBoxContainer(name + "_Content")
        # Internal auto-management
        super().add_child(self.content_node)

    def add_child(self, child):
        """Proxy add_child to the internal content container."""
        if child is self.content_node:
            super().add_child(child)
        else:
            self.content_node.add_child(child)
            
    def remove_child(self, child):
        self.content_node.remove_child(child)

    def perform_layout(self):
        super().perform_layout()
        
        # Enforce content size policy
        if self.content_node.size_policy_x == SizePolicy.FILL:
            self.content_node.width = self.width
            
        # Apply scroll offset to the content's position
        self.content_node.local_x = -self.scroll_x
        self.content_node.local_y = -self.scroll_y
        self.content_node.update_transforms()

    def clamp_scroll(self):
        max_scroll_x = max(0.0, self.content_node.width - self.width)
        max_scroll_y = max(0.0, self.content_node.height - self.height)
        self.scroll_x = max(0.0, min(self.scroll_x, max_scroll_x))
        self.scroll_y = max(0.0, min(self.scroll_y, max_scroll_y))
        
    def scroll(self, dx: float, dy: float):
        self.scroll_x += dx
        self.scroll_y += dy
        self.clamp_scroll()
        self.mark_layout_dirty()

    def render(self, surface):
        """Provides a clipping region for children during rendering."""
        from src.engine.core.engine import Engine
        renderer = Engine.instance.renderer if Engine.instance else None
        if not renderer: return
        
        sx, sy = self.get_screen_position()
        
        # Save previous clip, set new clip
        old_clip = renderer.get_clip(surface)
        renderer.set_clip(surface, sx, sy, self.width, self.height)
        
        # Render children
        for child in self.children:
            child.render(surface)
            
        # Restore old clip
        if old_clip:
            renderer.set_clip(surface, *old_clip)
        else:
            renderer.clear_clip(surface)
            
        # We don't call super().render because we already rendered the children manually
