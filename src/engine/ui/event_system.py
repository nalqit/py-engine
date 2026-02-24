from typing import Optional
from src.engine.ui.ui_node import UINode

class UIEvent:
    """Base class for UI events (Mouse, Keyboard, Focus)."""
    def __init__(self):
        self._consumed = False

    def consume(self):
        """Consume the event to stop further propagation."""
        self._consumed = True

    @property
    def is_consumed(self) -> bool:
        return self._consumed


class UIMouseEvent(UIEvent):
    """
    Mouse event payload containing screen coordinates 
    and the action type (down, up, move).
    """
    def __init__(self, x: float, y: float):
        super().__init__()
        self.x = x
        self.y = y


class UIKeyEvent(UIEvent):
    def __init__(self, key: int):
        super().__init__()
        self.key = key


class EventPropagationSystem:
    """
    Engine service that traverses the UI tree, hit-tests mouse events,
    and dispatches them bottom-up (bubbling) or directly to the focused node.
    """
    
    def __init__(self, engine: 'Engine'):
        self.engine = engine
        self._hovered_node: Optional[UINode] = None
        self._focused_node: Optional[UINode] = None
        self._mouse_down_node: Optional[UINode] = None

    def set_focus(self, node: Optional[UINode]):
        if self._focused_node != node:
            if self._focused_node and hasattr(self._focused_node, "on_focus_lost"):
                self._focused_node.on_focus_lost()
            self._focused_node = node
            if self._focused_node and hasattr(self._focused_node, "on_focus_gained"):
                self._focused_node.on_focus_gained()

    def process_events(self, root: 'Node'):
        """
        Called once per frame (usually before game update).
        Dispatches all UI events for the current frame.
        """
        inp = self.engine.input
        mx, my = inp.get_mouse_pos()
        
        # 1. Hit Test for hover
        current_hover = self._hit_test_recursive(root, mx, my)
        
        # 2. Handle Enter/Exit
        if current_hover != self._hovered_node:
            if self._hovered_node and hasattr(self._hovered_node, "on_mouse_exit"):
                self._hovered_node.on_mouse_exit()
            
            self._hovered_node = current_hover
            
            if self._hovered_node and hasattr(self._hovered_node, "on_mouse_enter"):
                self._hovered_node.on_mouse_enter()
                
        # 3. Handle Mouse Down / Up / Click
        # We check button 0 (Left click) by default
        if inp.is_mouse_just_pressed(0):
            self._mouse_down_node = current_hover
            if current_hover:
                event = UIMouseEvent(mx, my)
                self._bubble_event(current_hover, "on_mouse_down", event)
                # Give focus to clicked node (if it wants it, or remove focus if clicking empty space)
                # But actual focus logic typically requires widget opt-in. We'll set focus if clicked.
                self.set_focus(current_hover)
                
                # Consume input so the game doesn't shoot/jump behind the UI
                if event.is_consumed:
                    inp.consume_mouse(0)

        elif inp.is_mouse_just_released(0):
            if current_hover:
                event = UIMouseEvent(mx, my)
                self._bubble_event(current_hover, "on_mouse_up", event)
                
                # If mouse down AND up happened on the same node, it's a Click
                if current_hover == self._mouse_down_node:
                    click_event = UIMouseEvent(mx, my)
                    self._bubble_event(current_hover, "on_click", click_event)
                    if click_event.is_consumed:
                        inp.consume_mouse(0) # In case release implies more logic
                        
            self._mouse_down_node = None

        # 4. Handle Keyboard (route directly to focus)
        # In a real system, we'd iterate over all key events.
        # Here we just pass the raw input state to the focused node if it implements on_key
        if self._focused_node and hasattr(self._focused_node, "on_key"):
            # We don't have an event queue in this engine, we poll state.
            pass # Focus system will be fleshed out by widgets (e.g., text fields checking keys)

    def _hit_test_recursive(self, node: 'Node', mx: float, my: float) -> Optional[UINode]:
        """
        Walks the tree front-to-back (reverse children order is typically rendered last/on top).
        Returns the deepest UINode that contains the point.
        """
        # Search backwards so top-most rendered things get hit first
        for child in reversed(node.children):
            hit = self._hit_test_recursive(child, mx, my)
            if hit: return hit
            
        if isinstance(node, UINode):
            # Check bounding box
            sx, sy = node.get_screen_position()
            if sx <= mx <= sx + node.width and sy <= my <= sy + node.height:
                # Also check clipping if node has a custom hit-test (e.g. ScrollContainer)
                return node
                
        return None

    def _bubble_event(self, target: UINode, method_name: str, event: UIEvent):
        """Walks up the tree from target, calling method_name until consumed."""
        current = target
        while current and isinstance(current, UINode):
            if hasattr(current, method_name):
                # Call the handler handler
                handler = getattr(current, method_name)
                handler(event)
                
            if event.is_consumed:
                break
                
            current = current.parent
