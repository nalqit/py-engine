from abc import ABC, abstractmethod

# Tweak 1: Movement threshold constant to prevent flickering and clarify logic.
MOVEMENT_THRESHOLD = 10.0

class PlayerState(ABC):
    """Base class for all player states."""
    
    def enter(self, player):
        pass

    def exit(self, player):
        pass

    @abstractmethod
    def update(self, player, delta):
        """Must return a new state if transitioning, otherwise None."""
        pass


class IdleState(PlayerState):
    def update(self, player, delta):
        if player.controller.wants_to_dash():
            return DashState()
            
        # → JumpState if velocity_y < 0
        if player.velocity_y < 0:
            return JumpState()
            
        # → FallState if not grounded and velocity_y > 0
        is_grounded = player.controller.is_grounded
        if not is_grounded and player.velocity_y > 0:
            return FallState()
            
        # → RunState if abs(velocity_x) > movement_threshold
        if abs(player.velocity_x) > MOVEMENT_THRESHOLD:
            return RunState()
            
        return None


class RunState(PlayerState):
    def update(self, player, delta):
        if player.controller.wants_to_dash():
            return DashState()
            
        # → JumpState if velocity_y < 0
        if player.velocity_y < 0:
            return JumpState()
            
        # → FallState if not grounded
        is_grounded = player.controller.is_grounded
        if not is_grounded:
            return FallState()
            
        # → IdleState if abs(velocity_x) <= threshold
        if abs(player.velocity_x) <= MOVEMENT_THRESHOLD:
            return IdleState()
            
        return None


class JumpState(PlayerState):
    def update(self, player, delta):
        if player.controller.wants_to_dash():
            return DashState()
            
        # → FallState if velocity_y > 0 (reached peak of jump)
        if player.velocity_y > 0:
            return FallState()
            
        return None


class DashState(PlayerState):
    def enter(self, player):
        player.controller.start_dash(player)
        
    def update(self, player, delta):
        # Continue dashing
        player.controller.update_dash(player, delta)
        
        # When dash finishes, transition to Fall or Idle
        if not player.controller.is_dashing:
            if player.controller.is_grounded:
                if abs(player.velocity_x) > MOVEMENT_THRESHOLD:
                    return RunState()
                return IdleState()
            else:
                return FallState()
        return None

class FallState(PlayerState):
    def update(self, player, delta):
        # → DashState if input and cooldown ready
        if player.controller.wants_to_dash():
            return DashState()
            
        is_grounded = player.controller.is_grounded
        
        if is_grounded:
            # → RunState if grounded and abs(velocity_x) > threshold
            if abs(player.velocity_x) > MOVEMENT_THRESHOLD:
                return RunState()
            # → IdleState if grounded and abs(velocity_x) <= threshold
            else:
                return IdleState()
                
        return None
