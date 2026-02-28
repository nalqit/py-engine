"""
Frog Hop — Trap entities.
Spikes, Saw, Fire, and Trampoline traps loaded from src/Free/Traps.
No direct pygame import — uses engine Renderer + AssetManager.
"""
import os
import math
from src.pyengine2D import Node2D, Collider2D, Engine
from src.pyengine2D.utils.asset_manager import AssetManager

_SRC = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
TRAPS_DIR = os.path.join(_SRC, "Free", "Traps")


class Trap(Node2D):
    """Base class for all traps."""
    SCALE = 2

    def __init__(self, name, x, y, collision_world, damage=True):
        super().__init__(name, x, y)
        self.collision_world = collision_world
        self.does_damage = damage
        self._player_ref = None    # set by level builder

    def set_player(self, player):
        self._player_ref = player

    def _hurt_player(self):
        if self._player_ref and self.does_damage:
            self._player_ref.die()


class Spikes(Trap):
    """Static spike trap — instant kill on touch."""

    def __init__(self, name, x, y, collision_world):
        super().__init__(name, x, y, collision_world, damage=True)

        # Load idle sprite
        path = os.path.join(TRAPS_DIR, "Spikes", "Idle.png")
        r = Engine.instance.renderer
        self._img = r.load_image(path)
        iw, ih = r.get_surface_size(self._img)
        self._fw = iw
        self._fh = ih

        # Collider covering the spike area
        col = Collider2D(f"{name}_Col", -(iw * self.SCALE) // 2, -(ih * self.SCALE)+35, iw * self.SCALE, ih * self.SCALE //2)
        col.layer = "trap"
        col.mask = {"player"}
        col.is_static = True
        col.is_trigger = True
        col.visible = True
        self.add_child(col)
        self._col = col

    def update(self, delta):
        if self.collision_world and self._player_ref:
            gx, gy = self.get_global_position()
            S = self.SCALE
            hw, hh = (self._fw * S) // 2, (self._fh * S) // 2
            hits = self.collision_world.query_rect(
                gx - hw, gy - hh, gx + hw, gy + hh, exclude=self._col
            )
            for h in hits:
                if h.layer == "player":
                    self._hurt_player()
                    break
        super().update(delta)

    def render(self, surface):
        r = Engine.instance.renderer if Engine.instance else None
        if not r:
            return super().render(surface)
        sx, sy = self.get_screen_position()
        S = self.SCALE
        draw_x = int(sx) - (self._fw * S) // 2
        draw_y = int(sy) - (self._fh * S) // 2
        r.scale_blit(surface, self._img, (draw_x, draw_y),
                     src_area=(0, 0, self._fw, self._fh),
                     dest_size=(self._fw * S, self._fh * S))
        super().render(surface)


class Saw(Trap):
    """Animated saw that patrols between two points."""

    def __init__(self, name, x, y, collision_world, end_x=None, end_y=None, speed=120):
        super().__init__(name, x, y, collision_world, damage=True)

        # Load animated sheet
        path = os.path.join(TRAPS_DIR, "Saw", "On (38x38).png")
        r = Engine.instance.renderer
        self._sheet = r.load_image(path)
        sheet_w, _ = r.get_surface_size(self._sheet)
        self._fw, self._fh = 38, 38
        self._frame_count = max(1, sheet_w // self._fw)
        self._frame = 0
        self._timer = 0.0
        self._fps = 10

        # Movement patrol
        self._start_x = float(x)
        self._start_y = float(y)
        self._end_x = float(end_x if end_x is not None else x)
        self._end_y = float(end_y if end_y is not None else y)
        self._speed = speed
        self._t = 0.0          # 0..1 progress along the path
        self._direction = 1    # 1 = toward end, -1 = toward start

        # Total path length
        dx = self._end_x - self._start_x
        dy = self._end_y - self._start_y
        self._path_len = math.sqrt(dx * dx + dy * dy) or 1.0

        # Collider
        col = Collider2D(f"{name}_Col", -(38 * self.SCALE) // 2, -(38 * self.SCALE) // 2, 38 * self.SCALE, 38 * self.SCALE)
        col.layer = "trap"
        col.mask = {"player"}
        col.is_static = True
        col.is_trigger = True
        col.visible = True
        self.add_child(col)
        self._col = col

    def update(self, delta):
        # Animate
        self._timer += delta
        spf = 1.0 / self._fps
        if self._timer >= spf:
            self._timer -= spf
            self._frame = (self._frame + 1) % self._frame_count

        # Move along patrol path
        step = (self._speed * delta) / self._path_len
        self._t += step * self._direction
        if self._t >= 1.0:
            self._t = 1.0
            self._direction = -1
        elif self._t <= 0.0:
            self._t = 0.0
            self._direction = 1

        self.local_x = self._start_x + (self._end_x - self._start_x) * self._t
        self.local_y = self._start_y + (self._end_y - self._start_y) * self._t

        # Check player collision
        if self.collision_world and self._player_ref:
            gx, gy = self.get_global_position()
            S = self.SCALE
            hw, hh = (self._fw * S) // 2, (self._fh * S) // 2
            hits = self.collision_world.query_rect(
                gx - hw, gy - hh, gx + hw, gy + hh, exclude=self._col
            )
            for h in hits:
                if h.layer == "player":
                    self._hurt_player()
                    break

        super().update(delta)

    def render(self, surface):
        r = Engine.instance.renderer if Engine.instance else None
        if not r:
            return super().render(surface)
        sx, sy = self.get_screen_position()
        S = self.SCALE
        draw_x = int(sx) - (self._fw * S) // 2
        draw_y = int(sy) - (self._fh * S) // 2
        r.scale_blit(surface, self._sheet, (draw_x, draw_y),
                     src_area=(self._frame * self._fw, 0, self._fw, self._fh),
                     dest_size=(self._fw * S, self._fh * S))
        super().render(surface)


class Fire(Trap):
    """Animated fire trap — damages on contact while active."""

    def __init__(self, name, x, y, collision_world):
        super().__init__(name, x, y, collision_world, damage=True)

        r = Engine.instance.renderer
        path_on = os.path.join(TRAPS_DIR, "Fire", "On (16x32).png")
        self._sheet = r.load_image(path_on)
        sheet_w, _ = r.get_surface_size(self._sheet)
        self._fw, self._fh = 16, 32
        self._frame_count = max(1, sheet_w // self._fw)
        self._frame = 0
        self._timer = 0.0
        self._fps = 10

        col = Collider2D(f"{name}_Col", -(16 * self.SCALE) // 2, -(32 * self.SCALE) // 2, 16 * self.SCALE, 32 * self.SCALE)
        col.layer = "trap"
        col.mask = {"player"}
        col.is_static = True
        col.is_trigger = True
        col.visible = True
        self.add_child(col)
        self._col = col

    def update(self, delta):
        self._timer += delta
        spf = 1.0 / self._fps
        if self._timer >= spf:
            self._timer -= spf
            self._frame = (self._frame + 1) % self._frame_count

        if self.collision_world and self._player_ref:
            gx, gy = self.get_global_position()
            S = self.SCALE
            hw, hh = (self._fw * S) // 2, (self._fh * S) // 2
            hits = self.collision_world.query_rect(
                gx - hw, gy - hh, gx + hw, gy + hh, exclude=self._col
            )
            for h in hits:
                if h.layer == "player":
                    self._hurt_player()
                    break
        super().update(delta)

    def render(self, surface):
        r = Engine.instance.renderer if Engine.instance else None
        if not r:
            return super().render(surface)
        sx, sy = self.get_screen_position()
        S = self.SCALE
        draw_x = int(sx) - (self._fw * S) // 2
        draw_y = int(sy) - (self._fh * S) // 2
        r.scale_blit(surface, self._sheet, (draw_x, draw_y),
                     src_area=(self._frame * self._fw, 0, self._fw, self._fh),
                     dest_size=(self._fw * S, self._fh * S))
        super().render(surface)


class Trampoline(Trap):
    """Trampoline — bounces the player high into the air instead of dealing damage."""

    BOUNCE_FORCE = -1100.0  # stronger than normal jump

    def __init__(self, name, x, y, collision_world):
        super().__init__(name, x, y, collision_world, damage=False)

        r = Engine.instance.renderer
        path_idle = os.path.join(TRAPS_DIR, "Trampoline", "Idle.png")
        self._idle_img = r.load_image(path_idle)
        iw, ih = r.get_surface_size(self._idle_img)
        self._fw = iw
        self._fh = ih

        path_jump = os.path.join(TRAPS_DIR, "Trampoline", "Jump (28x28).png")
        self._jump_sheet = r.load_image(path_jump)
        jw, _ = r.get_surface_size(self._jump_sheet)
        self._jump_fw, self._jump_fh = 28, 28
        self._jump_frames = max(1, jw // 28)

        self._bouncing = False
        self._bounce_frame = 0
        self._bounce_timer = 0.0
        self._bounce_fps = 14

        # User custom collider positioning to match bottom half of trampoline
        col = Collider2D(f"{name}_Col", -(iw * self.SCALE) // 2, -(ih * self.SCALE) + 35, iw * self.SCALE, ih * self.SCALE // 2)
        col.layer = "trap"
        col.mask = {"player"}
        col.is_static = True
        col.is_trigger = True
        col.visible = True
        self.add_child(col)
        self._col = col

    def update(self, delta):
        # Animate bounce
        if self._bouncing:
            self._bounce_timer += delta
            spf = 1.0 / self._bounce_fps
            if self._bounce_timer >= spf:
                self._bounce_timer -= spf
                self._bounce_frame += 1
                if self._bounce_frame >= self._jump_frames:
                    self._bouncing = False
                    self._bounce_frame = 0

        # Check player overlap
        if self.collision_world and self._player_ref:
            gx, gy = self.get_global_position()
            S = self.SCALE
            hw, hh = (self._fw * S) // 2, (self._fh * S) // 2
            hits = self.collision_world.query_rect(
                gx - hw, gy - hh, gx + hw, gy + hh, exclude=self._col
            )
            for h in hits:
                if h.layer == "player":
                    self._player_ref.velocity_y = self.BOUNCE_FORCE
                    self._bouncing = True
                    self._bounce_frame = 0
                    self._bounce_timer = 0.0
                    break
        super().update(delta)

    def render(self, surface):
        r = Engine.instance.renderer if Engine.instance else None
        if not r:
            return super().render(surface)
        sx, sy = self.get_screen_position()
        S = self.SCALE

        if self._bouncing:
            fw, fh = self._jump_fw, self._jump_fh
            draw_x = int(sx) - (fw * S) // 2
            draw_y = int(sy) - (fh * S) // 2
            r.scale_blit(surface, self._jump_sheet, (draw_x, draw_y),
                         src_area=(self._bounce_frame * fw, 0, fw, fh),
                         dest_size=(fw * S, fh * S))
        else:
            fw, fh = self._fw, self._fh
            draw_x = int(sx) - (fw * S) // 2
            draw_y = int(sy) - (fh * S) // 2
            r.scale_blit(surface, self._img if hasattr(self, '_img') else self._idle_img,
                         (draw_x, draw_y),
                         src_area=(0, 0, fw, fh),
                         dest_size=(fw * S, fh * S))
        super().render(surface)
