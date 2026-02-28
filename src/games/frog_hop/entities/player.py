"""
Frog Hop — Player entity.
Animated Ninja Frog with Idle / Run / Jump / Fall states.
Uses engine AssetManager for loading — no direct pygame import.
"""
import os
from src.pyengine2D import PhysicsBody2D, Engine, Keys, Node2D
from src.pyengine2D.utils.asset_manager import AssetManager

_SRC = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
ASSETS = os.path.join(_SRC, "Free", "Main Characters", "Ninja Frog")


class Player(PhysicsBody2D):
    SCALE = 2  # scale 32x32 → 64x64 for visibility

    def __init__(self, name, x, y, collider, collision_world):
        super().__init__(name, x, y, collider, collision_world)
        self.use_gravity = True
        self.gravity = 1400.0
        self.move_speed = 300.0
        self.jump_force = -750.0
        self.facing_right = True
        self.score = 0
        self.lives = 3
        self.health = 3
        self.max_health = 3
        self.invulnerable_timer = 0.0
        self.spawn_point = (x, y)  # updated by level loader

        self.register_signal("on_score_changed")
        self.register_signal("on_lives_changed")
        self.register_signal("on_health_changed")
        self.register_signal("on_died")

        # Load sprite sheets via AssetManager
        am = AssetManager.instance()
        self._sheets = {}
        self._frame_counts = {}
        self._load_sheet(am, "idle",  "Idle (32x32).png",  11)
        self._load_sheet(am, "run",   "Run (32x32).png",   12)
        self._load_sheet(am, "jump",  "Jump (32x32).png",  1)
        self._load_sheet(am, "fall",  "Fall (32x32).png",  1)

        self._anim_state = "idle"
        self._frame = 0
        self._anim_timer = 0.0
        self._fps = 12

    def _load_sheet(self, am, key, filename, count):
        path = os.path.join(ASSETS, filename)
        sheet = am.load_image(path)
        self._sheets[key] = sheet
        self._frame_counts[key] = count

    # ---- gameplay ----

    def update(self, delta):
        inp = Engine.instance.input

        move = 0
        if inp.is_key_pressed(Keys.A) or inp.is_key_pressed(Keys.LEFT):
            move -= 1
        if inp.is_key_pressed(Keys.D) or inp.is_key_pressed(Keys.RIGHT):
            move += 1

        self.velocity_x = move * self.move_speed
        if move != 0:
            self.facing_right = move > 0

        # Decrease invulnerability timer
        if self.invulnerable_timer > 0:
            self.invulnerable_timer -= delta

        is_grounded = self._check_ground()

        if (inp.is_key_just_pressed(Keys.SPACE) or inp.is_key_just_pressed(Keys.W) or
                inp.is_key_just_pressed(Keys.UP)) and is_grounded:
            self.velocity_y = self.jump_force

        super().update(delta)

        prev_state = self._anim_state
        if not is_grounded:
            self._anim_state = "jump" if self.velocity_y < 0 else "fall"
        elif abs(self.velocity_x) > 10:
            self._anim_state = "run"
        else:
            self._anim_state = "idle"

        if self._anim_state != prev_state:
            self._frame = 0
            self._anim_timer = 0.0

        self._anim_timer += delta
        spf = 1.0 / self._fps
        if self._anim_timer >= spf:
            self._anim_timer -= spf
            self._frame = (self._frame + 1) % self._frame_counts[self._anim_state]

        if self.get_global_position()[1] > 1200:
            self.die()

        # Check enemy collision
        if self.collision_world:
            gx, gy = self.get_global_position()
            rect = self.collider.get_rect()
            hw = 23  # derived from Player collider -23 to 22 -> 45 width roughly / 2 = 22.5
            hh = 25  # height 50 / 2 = 25
            hits = self.collision_world.query_rect(
                gx - hw, gy - hh, gx + hw, gy + hh, exclude=self.collider
            )
            for h in hits:
                if h.layer == "enemy":
                    enemy = h.parent
                    if getattr(enemy, 'is_dead', False): continue
                    if self.invulnerable_timer > 0: continue

                    ey = enemy.get_global_position()[1]
                    # Check if stomping (falling & above enemy center)
                    if self.velocity_y > 0 and gy < ey - 10:
                        enemy.on_stomp()
                        self.velocity_y = -600  # Stomp bounce
                        self.score += 50
                        self.emit_signal("on_score_changed", score=self.score)
                    else:
                        self.take_damage(enemy.get_global_position()[0])

    def _check_ground(self):
        if not self.collision_world:
            return False
        rect = self.collider.get_rect()
        if isinstance(rect, tuple):
            gx, gy, gr, gb = rect
        else:
            gx, gy, gr, gb = rect.left, rect.top, rect.right, rect.bottom
        hits = self.collision_world.query_rect(gx + 2, gb, gr - 2, gb + 3, exclude=self.collider)
        for h in hits:
            if h.is_static and h.layer == "wall":
                return True
        return False

    def collect_fruit(self, value=10):
        self.score += value
        self.emit_signal("on_score_changed", score=self.score)

    def take_damage(self, source_x):
        if self.invulnerable_timer > 0:
            return  # i-frames active

        self.health -= 1
        self.emit_signal("on_health_changed", health=self.health)
        
        # Determine knockback direction
        dir_x = 1 if self.get_global_position()[0] > source_x else -1
        
        # Apply physics impulse (knockback)
        self.velocity_x = dir_x * 400
        self.velocity_y = -400
        
        # Set i-frames
        self.invulnerable_timer = 1.0

        if self.health <= 0:
            self.die()

    def die(self):
        self.lives -= 1
        self.health = self.max_health  # Reset health
        self.emit_signal("on_lives_changed", lives=self.lives)
        self.emit_signal("on_health_changed", health=self.health)
        if self.lives <= 0:
            self.emit_signal("on_died")
        self.local_x = self.spawn_point[0]
        self.local_y = self.spawn_point[1]
        self.velocity_x = 0
        self.velocity_y = 0
        self.invulnerable_timer = 2.0  # Safety window after respawn
        self.update_transforms()
        if hasattr(self, '_refresh_collider_cache'):
            self._refresh_collider_cache(self)

    # ---- rendering ----

    def render(self, surface):
        r = Engine.instance.renderer if Engine.instance else None
        if not r:
            super().render(surface)
            return

        sheet = self._sheets[self._anim_state]
        frame_w, frame_h = 32, 32
        src_area = (self._frame * frame_w, 0, frame_w, frame_h)

        sx, sy = self.get_screen_position()
        S = self.SCALE
        draw_x = int(sx) - (frame_w * S) // 2
        draw_y = int(sy) - (frame_h * S) // 2

        # Flicker effect during invulnerability
        if self.invulnerable_timer > 0:
            # Flicker based on remaining time (e.g. blink every 0.1s)
            if int(self.invulnerable_timer * 10) % 2 == 0:
                super().render(surface)
                return

        # Use renderer's scale_blit helper
        r.scale_blit(surface, sheet, (draw_x, draw_y),
                     src_area, (frame_w * S, frame_h * S),
                     flip_x=not self.facing_right)

        super().render(surface)
