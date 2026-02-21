from src.engine.physics.physics_body_2d import PhysicsBody2D

class PatrolEnemy(PhysicsBody2D):
    """
    A simple enemy that patrols left and right, turning around when hitting walls.
    Can be defeated by the player jumping on it.
    Demands the player to be "hurt" if touched from the side.
    """

    def __init__(self, name, x, y, collider, collision_world, speed=50.0):
        super().__init__(name, x, y, collider, collision_world)
        self.use_gravity = True
        self.speed = speed
        self.direction = -1.0  # Start by moving left
        self.is_dead = False

    def update(self, delta):
        if self.is_dead:
            return

        # Always try to move horizontally at constant speed
        self.velocity_x = self.speed * self.direction

        # Physics resolution (deals with collisions)
        super().update(delta)

        # If velocity_x became 0, we hit a wall!
        if self.velocity_x == 0:
            self.direction *= -1.0

    def on_collision_enter(self, other):
        if self.is_dead:
            return

        # Check if the other collider belongs to the player
        if other.layer == "player" and other.parent:
            player = other.parent
            
            # Simple check to see if player is falling strictly from above
            # We compare the bottoms of the colliders to ensure a stomp
            my_bounds = self.collider.get_rect()
            my_top = my_bounds.top + self.parent.get_global_position()[1] if self.parent else my_bounds.top
            
            # Actually our self.collider.get_rect() operates in local space relative to its owner,
            # or it might be easier to use global positions.
            # get_global_position() already includes parent offsets.
            # A simpler heuristic for this game:
            if player.velocity_y > 0 and player.get_global_position()[1] < self.get_global_position()[1]:
                # Player stomped on us!
                self.stomp(player)
            else:
                # Player touched us from the side or bottom!
                if hasattr(player, "die"):
                    player.die()

    def stomp(self, player):
        self.is_dead = True
        # Bounce the player up
        player.velocity_y = -400  # Jump impulse
        
        # Remove ourselves from the tree
        if self.parent:
            self.parent.remove_child(self)
