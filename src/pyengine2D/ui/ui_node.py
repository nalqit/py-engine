import enum
from src.pyengine2D.scene.node2d import Node2D


class Anchor(enum.Enum):
    TOP_LEFT = enum.auto()
    TOP_CENTER = enum.auto()
    TOP_RIGHT = enum.auto()
    CENTER_LEFT = enum.auto()
    CENTER = enum.auto()
    CENTER_RIGHT = enum.auto()
    BOTTOM_LEFT = enum.auto()
    BOTTOM_CENTER = enum.auto()
    BOTTOM_RIGHT = enum.auto()


class SizePolicy(enum.Enum):
    FIXED = enum.auto()      # Uses explicit width/height
    FILL = enum.auto()       # Expands to fill available space in parent container
    WRAP_CONTENT = enum.auto() # Shrinks to fit children (implemented per-container)


class UINode(Node2D):
    """
    Base class for all UI elements.
    Integrates with the engine's auto-layout system rather than relying
    solely on manual (x, y) coordinates.
    """

    def __init__(self, name: str, width: float = 100.0, height: float = 100.0):
        super().__init__(name, 0, 0)
        self.register_signal("on_resized")
        
        # Dimensions
        self._width = width
        self._height = height
        
        # Layout Rules
        self.anchor = Anchor.TOP_LEFT
        self.margin_top = 0.0
        self.margin_right = 0.0
        self.margin_bottom = 0.0
        self.margin_left = 0.0
        
        self.size_policy_x = SizePolicy.FIXED
        self.size_policy_y = SizePolicy.FIXED
        
        self.min_width = 0.0
        self.min_height = 0.0
        
        # Dirty flag for layout optimization
        self.is_layout_dirty = True

    @property
    def width(self) -> float:
        return self._width

    @width.setter
    def width(self, value: float):
        if self._width != value:
            self._width = max(self.min_width, value)
            self.mark_layout_dirty()
            self.emit_signal("on_resized", self._width, self._height)

    @property
    def height(self) -> float:
        return self._height

    @height.setter
    def height(self, value: float):
        if self._height != value:
            self._height = max(self.min_height, value)
            self.mark_layout_dirty()
            self.emit_signal("on_resized", self._width, self._height)

    def mark_layout_dirty(self):
        """Marks this node and all ancestors as needing a layout pass."""
        node = self
        while node and isinstance(node, UINode):
            node.is_layout_dirty = True
            node = node.parent

    def update(self, delta: float) -> None:
        """
        Overridden update to run the layout pass BEFORE children update.
        This ensures click regions and rendering match the current frame's
        resolved layout.
        """
        if self.is_layout_dirty:
            self.perform_layout()
            self.is_layout_dirty = False
            
        super().update(delta)

    def perform_layout(self):
        """
        Resolves layout for this node.
        Containers (VBox, HBox) will override this to position children.
        Base UINode just handles anchoring within its parent boundaries.
        """
        if not isinstance(self.parent, UINode):
            return  # If parent isn't UI, manual positioning is likely expected

        # If parent is a layout container (VBox, HBox, Grid), it manages our position.
        # We should NOT apply generic anchoring.
        if getattr(self.parent, "is_layout_container", False):
            return

        parent_w = self.parent.width
        parent_h = self.parent.height

        # Handle FILL policy (only applies if parent doesn't override via container logic)
        if self.size_policy_x == SizePolicy.FILL:
            self.width = max(self.min_width, parent_w - self.margin_left - self.margin_right)
        if self.size_policy_y == SizePolicy.FILL:
            self.height = max(self.min_height, parent_h - self.margin_top - self.margin_bottom)

        # Handle Anchoring
        target_x = self.margin_left
        target_y = self.margin_top

        # Horizontal Anchor
        if self.anchor in (Anchor.TOP_CENTER, Anchor.CENTER, Anchor.BOTTOM_CENTER):
            target_x = (parent_w / 2.0) - (self.width / 2.0)
        elif self.anchor in (Anchor.TOP_RIGHT, Anchor.CENTER_RIGHT, Anchor.BOTTOM_RIGHT):
            target_x = parent_w - self.width - self.margin_right

        # Vertical Anchor
        if self.anchor in (Anchor.CENTER_LEFT, Anchor.CENTER, Anchor.CENTER_RIGHT):
            target_y = (parent_h / 2.0) - (self.height / 2.0)
        elif self.anchor in (Anchor.BOTTOM_LEFT, Anchor.BOTTOM_CENTER, Anchor.BOTTOM_RIGHT):
            target_y = parent_h - self.height - self.margin_bottom

        self.local_x = target_x
        self.local_y = target_y
        self.update_transforms()
