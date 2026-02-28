"""
Frog Hop — Enemy entity.
Patrols horizontally, turns on ledges or walls.
Handles deferred removal on stomp.
"""
import os
from src.pyengine2D import PhysicsBody2D, Collider2D, Engine

_SRC = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))

class Enemy(PhysicsBody2D):
    SCALE = 2

    def __init__(self, name, x, y, collision_world, enemy_type="Mask Dude", speed=100.0, **kwargs):
        # We need to setup collider properly
        col = Collider2D(f"{name}_Col", -16, -16, 32, 32)
        col.layer = "enemy"
        col.mask = {"wall"}
        col.visible = False
        
        super().__init__(name, x, y, col, collision_world)
        self.add_child(col)
        
        self.use_gravity = True
        self.gravity = 1400.0
        self.speed = speed
        self.direction = -1  # start left
        self.is_dead = False
        self._death_timer = 0.0
        
        # Animations
        base_path = os.path.join(_SRC, "Free", "Main Characters", enemy_type)
        r = Engine.instance.renderer
        
        self._sheets = {}
        self._frame_counts = {}
        
        self._load_sheet(r, "run", os.path.join(base_path, "Run (32x32).png"), 12)
        self._load_sheet(r, "hit", os.path.join(base_path, "Hit (32x32).png"), 7)
        
        self._anim_state = "run"
        self._frame = 0
        self._anim_timer = 0.0
        self._fps = 14
        
    def _load_sheet(self, r, key, path, count):
        if not os.path.exists(path):
            self._sheets[key] = None
            self._frame_counts[key] = 1
            return
        sheet = r.load_image(path)
        self._sheets[key] = sheet
        self._frame_counts[key] = count

    def update(self, delta):
        if self.is_dead:
            self._anim_state = "hit"
            self._death_timer -= delta
            super().update(delta)
            
            # Animate death
            self._anim_timer += delta
            spf = 1.0 / self._fps
            if self._anim_timer >= spf:
                self._anim_timer -= spf
                self._frame = min(self._frame + 1, self._frame_counts["hit"] - 1)
                
            if self._death_timer <= 0:
                if self.parent:
                    self.parent.remove_child(self)
            return

        # Patrol logic
        self.velocity_x = self.speed * self.direction
        
        if self.collision_world:
            gx, gy = self.get_global_position()
            hw = 16 * self.SCALE
            hh = 16 * self.SCALE
            
            # Wall probe
            wall_probe_x = gx + (hw + 2) * self.direction
            wall_hits = self.collision_world.query_rect(
                wall_probe_x - 2, gy - 2, wall_probe_x + 2, gy + hh - 4, exclude=self.collider
            )
            hit_wall = any(h.is_static and h.layer == "wall" for h in wall_hits)
            
            # Ledge probe
            ledge_probe_x = gx + (hw + 4) * self.direction
            ledge_probe_y = gy + hh + 4
            ledge_hits = self.collision_world.query_rect(
                ledge_probe_x - 2, ledge_probe_y - 2, ledge_probe_x + 2, ledge_probe_y + 2, exclude=self.collider
            )
            hit_ledge = any(h.is_static and h.layer == "wall" for h in ledge_hits)
            
            # If hit wall OR no floor ahead, reverse!
            if hit_wall or not hit_ledge:
                self.direction *= -1
                self.velocity_x = self.speed * self.direction

        super().update(delta)

        # Animate
        self._anim_timer += delta
        spf = 1.0 / self._fps
        if self._anim_timer >= spf:
            self._anim_timer -= spf
            self._frame = (self._frame + 1) % self._frame_counts[self._anim_state]

    def on_stomp(self):
        if self.is_dead: return
        self.is_dead = True
        self.collider.is_trigger = True  # Disable physics collisions
        self._death_timer = 0.3  # Remove after 0.3s
        self.velocity_x = 0
        self._frame = 0

    def render(self, surface):
        r = Engine.instance.renderer if Engine.instance else None
        if not r:
            super().render(surface)
            return

        sheet = self._sheets.get(self._anim_state)
        if not sheet:
            super().render(surface)
            return
            
        frame_w, frame_h = 32, 32
        src_area = (self._frame * frame_w, 0, frame_w, frame_h)

        sx, sy = self.get_screen_position()
        S = self.SCALE
        draw_x = int(sx) - (frame_w * S) // 2
        draw_y = int(sy) - (frame_h * S) // 2

        r.scale_blit(surface, sheet, (draw_x, draw_y),
                     src_area, (frame_w * S, frame_h * S),
                     flip_x=(self.direction > 0))

        super().render(surface)
