class PlayerController:
    """
    Gameplay-level controller for the Player entity.
    Respects Level 4 architectural rules:
    - Engine-agnostic (no pygame imports)
    - Non-invasive ground detection
    - High-level properties (acceleration, friction, etc.)
    """

    def __init__(self):
        # Movement properties
        self.acceleration = 1200.0
        self.max_speed = 400.0
        self.friction = 800.0
        self.jump_force = 450.0
        
        # Dash properties
        self.dash_speed = 800.0
        self.dash_duration = 0.2
        self.dash_cooldown = 1.0

        # Internal state
        self._grounded = False
        self.facing_right = True
        
        self.is_dashing = False
        self._dash_timer = 0.0
        self._dash_cooldown_timer = 0.0
        self._wants_to_dash = False

    def update(self, player, delta, input_state):
        """
        Main logic loop.
        input_state: dict with keys 'move_left', 'move_right', 'jump', 'dash'
        """
        self._update_grounded(player)
        
        # Cooldown management
        if self._dash_cooldown_timer > 0:
            self._dash_cooldown_timer -= delta
            
        # Register dash intent
        self._wants_to_dash = input_state.get("dash", False) and self._dash_cooldown_timer <= 0
        
        # Facing direction
        if input_state.get("move_right", False):
            self.facing_right = True
        elif input_state.get("move_left", False):
            self.facing_right = False
            
        if not self.is_dashing:
            self._handle_horizontal_movement(player, delta, input_state)
            self._handle_jump(player, input_state)

    def _update_grounded(self, player):
        """Pure probe check for ground detection."""
        probe_offset = 2.0
        result = player.collision_world.check_collision(
            player.collider,
            player.local_x,
            player.local_y + probe_offset
        )
        self._grounded = result.collided and result.normal_y < 0

    def _handle_horizontal_movement(self, player, delta, input_state):
        move_dir = 0
        if input_state.get("move_left", False):
            move_dir -= 1
        if input_state.get("move_right", False):
            move_dir += 1

        if move_dir != 0:
            # Accelerate
            player.velocity_x += move_dir * self.acceleration * delta
            # Clamp to max speed
            if abs(player.velocity_x) > self.max_speed:
                player.velocity_x = (player.velocity_x / abs(player.velocity_x)) * self.max_speed
        else:
            # Apply friction
            if player.velocity_x > 0:
                player.velocity_x = max(0, player.velocity_x - self.friction * delta)
            elif player.velocity_x < 0:
                player.velocity_x = min(0, player.velocity_x + self.friction * delta)

    def _handle_jump(self, player, input_state):
        if input_state.get("jump", False) and self._grounded:
            # Override vertical velocity instead of adding to it.
            # This prevents jump power from being reduced if the jump is triggered
            # just 1 frame before hitting the floor (jump buffering/coyote time).
            player.velocity_y = -self.jump_force
            self._grounded = False  # Immediate exit from grounded state

    @property
    def is_grounded(self):
        return self._grounded
        
    def wants_to_dash(self):
        return self._wants_to_dash
        
    def start_dash(self, player):
        self.is_dashing = True
        self._dash_timer = self.dash_duration
        self._dash_cooldown_timer = self.dash_cooldown
        
        # Eliminate vertical speed for a pure horizontal dash
        player.velocity_y = 0.0
        
        # Give immediate burst of speed in facing direction
        dir_mult = 1.0 if self.facing_right else -1.0
        player.velocity_x = self.dash_speed * dir_mult
        
        # Disable gravity temporarily
        player.use_gravity = False
        
        # Audio/Visual juice: Squash stretch during dash
        if hasattr(player, "apply_juice"):
            player.apply_juice(1.4, 0.6, self.dash_duration)
            
    def update_dash(self, player, delta):
        if not self.is_dashing: return
        
        self._dash_timer -= delta
        
        # Add a trail of particles
        if hasattr(player, "dash_effect"):
            player.dash_effect()
        
        # Force continuous velocity
        dir_mult = 1.0 if self.facing_right else -1.0
        player.velocity_x = self.dash_speed * dir_mult
        player.velocity_y = 0.0  # stay in the air
        
        if self._dash_timer <= 0:
            self.is_dashing = False
            # Re-enable gravity
            player.use_gravity = True
            # Brake suddenly for tight control
            player.velocity_x *= 0.2
