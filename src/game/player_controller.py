class PlayerController:
    def __init__(self):
        self.acceleration = 1200.0
        self.max_speed = 400.0
        self.friction = 800.0
        self.is_grounded = False
        self.facing_right = True
        
    def update(self, player, delta, input_state):
        # 1. Ground detection
        self.is_grounded = self._check_ground(player)
        
        # 2. Horizontal movement
        move_dir = 0
        if input_state.get("move_left", False):
            move_dir -= 1
        if input_state.get("move_right", False):
            move_dir += 1
            
        if move_dir != 0:
            player.velocity_x += move_dir * self.acceleration * delta
            if player.velocity_x > self.max_speed:
                player.velocity_x = self.max_speed
            elif player.velocity_x < -self.max_speed:
                player.velocity_x = -self.max_speed
            self.facing_right = move_dir > 0
        else:
            # Friction
            old_sign = 1 if player.velocity_x > 0 else -1
            player.velocity_x -= old_sign * self.friction * delta
            if (old_sign == 1 and player.velocity_x < 0) or (old_sign == -1 and player.velocity_x > 0):
                player.velocity_x = 0.0

        # 3. Jumping
        if input_state.get("jump", False) and self.is_grounded:
            jump_f = player.jump_force if hasattr(player, "jump_force") else -450.0
            player.velocity_y = jump_f
            self.is_grounded = False

    def _check_ground(self, player):
        if not hasattr(player, "collision_world") or not player.collision_world:
            return False
            
        # Probe directly below the player
        res = player.collider.get_rect()
        if isinstance(res, tuple):
             gx, gy, gr, gb = res
        else:
             gx, gy, gr, gb = res.left, res.top, res.right, res.bottom
             
        probe_left = gx + 2
        probe_right = gr - 2
        probe_top = gb
        probe_bottom = gb + 2.0
        
        hits = player.collision_world.query_rect(probe_left, probe_top, probe_right, probe_bottom, exclude=player.collider)
        
        for h in hits:
            if h.is_static and h.layer in {"wall", "box"}:
                return True
                
        return False
