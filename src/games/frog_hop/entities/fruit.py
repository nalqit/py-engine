"""
Frog Hop — Animated Fruit collectible.
Apple.png is 544x32 = 17 frames of 32x32.
No direct pygame import — uses engine Renderer + AssetManager.
"""
import os
from src.pyengine2D import Node2D, CircleCollider2D, Engine

_SRC = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
FRUIT_DIR = os.path.join(_SRC, "Free", "Items", "Fruits")

FRUITS = ["Apple", "Cherries", "Orange", "Strawberry", "Bananas", "Kiwi", "Melon", "Pineapple"]


class Fruit(Node2D):
    SCALE = 2

    def __init__(self, name, x, y, collision_world, fruit_name="Apple"):
        super().__init__(name, x, y)
        self.collision_world = collision_world
        self.collected = False
        self.register_signal("on_collected")

        # Load animated sheet via engine renderer
        path = os.path.join(FRUIT_DIR, f"{fruit_name}.png")
        r = Engine.instance.renderer
        self._sheet = r.load_image(path)
        sheet_w, _ = r.get_surface_size(self._sheet)
        self._frame_count = sheet_w // 32
        self._frame = 0
        self._timer = 0.0
        self._fps = 14

        # Trigger collider
        self._col = CircleCollider2D(f"{name}_Col", 0, 0, 15)
        self._col.layer = "pickup"
        self._col.mask = {"player"}
        self._col.is_static = False
        self._col.is_trigger = True
        self._col.visible = True
        self.add_child(self._col)

    def update(self, delta):
        if self.collected:
            return

        # Animate
        self._timer += delta
        if self._timer >= 1.0 / self._fps:
            self._timer -= 1.0 / self._fps
            self._frame = (self._frame + 1) % self._frame_count

        # Check overlap with player via rect query
        if self.collision_world:
            gx, gy = self.get_global_position()
            r = 20
            hits = self.collision_world.query_rect(gx - r, gy - r, gx + r, gy + r, exclude=self._col)
            for h in hits:
                if h.layer == "player":
                    self._collect()
                    return

        super().update(delta)

    def _collect(self):
        self.collected = True
        self.emit_signal("on_collected")
        if self.parent:
            self.parent.remove_child(self)

    def render(self, surface):
        if self.collected:
            return

        fw, fh = 32, 32
        S = self.SCALE
        sx, sy = self.get_screen_position()
        draw_x = int(sx) - (fw * S) // 2
        draw_y = int(sy) - (fh * S) // 2

        r = Engine.instance.renderer if Engine.instance else None
        if r:
            r.scale_blit(surface, self._sheet, (draw_x, draw_y),
                         src_area=(self._frame * fw, 0, fw, fh),
                         dest_size=(fw * S, fh * S))

        super().render(surface)
