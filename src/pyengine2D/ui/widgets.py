from typing import Optional, Tuple, Callable
from src.pyengine2D.ui.ui_node import UINode, Anchor, SizePolicy
from src.pyengine2D.ui.data_binding import ObservableModel, DataBinding

Color = Tuple[int, int, int]

class UIPanel(UINode):
    """A rectangular background panel with optional border."""
    def __init__(self, name: str, width: float, height: float, bg_color: Color = (50, 50, 60), border_color: Optional[Color] = None, border_width: int = 1):
        super().__init__(name, width, height)
        self.bg_color = bg_color
        self.border_color = border_color
        self.border_width = border_width

    def render(self, surface):
        from src.pyengine2D.core.engine import Engine
        renderer = Engine.instance.renderer if Engine.instance else None
        if not renderer: return
        
        sx, sy = self.get_screen_position()
        
        # We use Renderer's primitive drawing
        if self.bg_color:
            renderer.draw_rect(surface, self.bg_color, sx, sy, self.width, self.height)
            
        if self.border_color and self.border_width > 0:
            renderer.draw_rect(surface, self.border_color, sx, sy, self.width, self.height, self.border_width)
            
        super().render(surface)


class UILabel(UINode):
    """Text label with data binding support. Word wrap omitted for simplicity."""
    def __init__(self, name: str, text: str = "", font_size: int = 16, color: Color = (255, 255, 255)):
        super().__init__(name, width=0, height=0)
        self._text = text
        self.font_size = font_size
        self.color = color
        self.bold = False
        self._binding: Optional[DataBinding] = None
        
        # UILabel defaults to wrap content
        self.size_policy_x = SizePolicy.WRAP_CONTENT
        self.size_policy_y = SizePolicy.WRAP_CONTENT
        self._cache_size()

    @property
    def text(self):
        return self._text
        
    @text.setter
    def text(self, val: str):
        if self._text != str(val):
            self._text = str(val)
            self._cache_size()
            self.mark_layout_dirty()

    def bind(self, model: ObservableModel, prop_name: str, formatter: Callable = str):
        if self._binding:
            self._binding.unbind()
        
        # DataBinding calls self.text = formatted(value) automatically
        self._binding = DataBinding(self, lambda text: setattr(self, 'text', text), model, prop_name, formatter)

    def _cache_size(self):
        from src.pyengine2D.ui.font_cache import FontCache
        surf = FontCache.get_text_surface(self._text, self.color, self.font_size, self.bold)
        if surf:
            # We want minimum size to reflect text size
            self.min_width = surf.get_width()
            self.min_height = surf.get_height()
            
            # If wrap_content, update real width/height
            if self.size_policy_x == SizePolicy.WRAP_CONTENT:
                self._width = max(self.width, self.min_width)
            if self.size_policy_y == SizePolicy.WRAP_CONTENT:
                self._height = max(self.height, self.min_height)

    def render(self, surface):
        from src.pyengine2D.core.engine import Engine
        renderer = Engine.instance.renderer if Engine.instance else None
        if not renderer: return
        
        sx, sy = self.get_screen_position()
        renderer.draw_text(surface, self._text, self.color, sx, sy, self.font_size, self.bold)
        super().render(surface)


class UIButton(UIPanel):
    """Interactive button with hover states and click signals."""
    def __init__(self, name: str, text: str, width: float = 120, height: float = 40):
        super().__init__(name, width, height, bg_color=(80, 80, 90), border_color=(200, 200, 200), border_width=1)
        self.register_signal("on_pressed")
        
        self.normal_color = (80, 80, 90)
        self.hover_color = (110, 110, 130)
        self.pressed_color = (50, 50, 60)
        
        self.label = UILabel(name + "_label", text)
        self.label.anchor = Anchor.CENTER
        self.label.is_layout_container = True  # We manual layout it using center anchor
        
        self.add_child(self.label)

    def on_mouse_enter(self):
        self.bg_color = self.hover_color

    def on_mouse_exit(self):
        self.bg_color = self.normal_color

    def on_mouse_down(self, event):
        self.bg_color = self.pressed_color
        event.consume()

    def on_mouse_up(self, event):
        self.bg_color = self.hover_color

    def on_click(self, event):
        self.bg_color = self.hover_color
        self.emit_signal("on_pressed")
        event.consume()


class UIProgressBar(UIPanel):
    """Filled progress bar."""
    def __init__(self, name: str, width: float = 200, height: float = 20):
        super().__init__(name, width, height, bg_color=(30, 30, 30), border_color=(200, 200, 200))
        self.fill_color = (50, 200, 50)
        self._progress = 0.0 # 0.0 to 1.0
        self._binding: Optional[DataBinding] = None

    @property
    def progress(self):
        return self._progress
        
    @progress.setter
    def progress(self, val: float):
        self._progress = max(0.0, min(1.0, float(val)))

    def bind(self, model: ObservableModel, prop_name: str, formatter: Callable = float):
        if self._binding:
            self._binding.unbind()
        self._binding = DataBinding(self, lambda p: setattr(self, 'progress', p), model, prop_name, formatter)

    def render(self, surface):
        super().render(surface)
        if self.progress <= 0: return
        
        from src.pyengine2D.core.engine import Engine
        renderer = Engine.instance.renderer if Engine.instance else None
        if not renderer: return

        sx, sy = self.get_screen_position()
        fill_w = int(self.width * self.progress)
        # Pad slightly to sit inside the border
        pad = 2
        renderer.draw_rect(surface, self.fill_color, sx+pad, sy+pad, max(0, fill_w - pad*2), max(0, int(self.height) - pad*2))

class UIListView(UINode):
    """
    Virtual scrolling list view.
    Instead of 10,000 nodes, it creates just enough UINodes to fill the visible area
    plus a few buffer rows, and pools them based on scroll position.
    """
    def __init__(self, name: str, width: float, height: float, row_height: float, item_class: type = UILabel):
        super().__init__(name, width, height)
        self.row_height = row_height
        self.item_class = item_class
        self.items = [] # Data list
        
        self.scroll_y = 0.0
        
        # We need a clip rect, so we act like a ScrollContainer
        self.is_layout_container = True
        
        self.visible_rows = int(height / row_height) + 2
        self.row_widgets = []
        
        for i in range(self.visible_rows):
            # Instantiate pool of widget rows
            try:
                widget = item_class(f"{name}_Row_{i}", "")
            except TypeError:
                widget = item_class(f"{name}_Row_{i}")
                
            widget.parent = self
            widget.is_layout_container = False 
            self.children.append(widget)
            self.row_widgets.append(widget)

    def set_items(self, items: list):
        self.items = items
        self.scroll_y = 0.0
        self.mark_layout_dirty()

    def scroll(self, dy: float):
        max_scroll = max(0.0, len(self.items) * self.row_height - self.height)
        self.scroll_y = max(0.0, min(self.scroll_y + dy, max_scroll))
        self.mark_layout_dirty()

    def perform_layout(self):
        super().perform_layout()
        
        # Determine which items are visible
        start_idx = int(self.scroll_y / self.row_height)
        offset_y = self.scroll_y % self.row_height
        
        for i, widget in enumerate(self.row_widgets):
            item_idx = start_idx + i
            if item_idx < len(self.items):
                widget.visible = True
                if hasattr(widget, "text"):
                    widget.text = str(self.items[item_idx])
                
                widget.local_x = 0
                widget.local_y = (i * self.row_height) - offset_y
                if widget.size_policy_x == SizePolicy.FILL:
                    widget.width = self.width
                if widget.size_policy_y == SizePolicy.FILL:
                    widget.height = self.row_height
                    
                widget.update_transforms()
            else:
                widget.visible = False

    def render(self, surface):
        from src.pyengine2D.core.engine import Engine
        renderer = Engine.instance.renderer if Engine.instance else None
        if not renderer: return
        
        sx, sy = self.get_screen_position()
        
        old_clip = renderer.get_clip(surface)
        renderer.set_clip(surface, sx, sy, self.width, self.height)
        
        for widget in self.row_widgets:
            if getattr(widget, "visible", True):
                widget.render(surface)
                
        if old_clip:
            renderer.set_clip(surface, *old_clip)
        else:
            renderer.clear_clip(surface)
