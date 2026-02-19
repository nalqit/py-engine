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

        # Internal state
        self._grounded = False

    def update(self, player, delta, input_state):
        """
        Main logic loop.
        input_state: dict with keys 'move_left', 'move_right', 'jump'
        """
        self._update_grounded(player)
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
            # Apply upward impulse
            player.apply_impulse(0, -self.jump_force)
            self._grounded = False  # Immediate exit from grounded state

    @property
    def is_grounded(self):
        return self._grounded
