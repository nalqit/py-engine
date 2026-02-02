import pygame

class DebugDraw:
    def __init__(self, parent_node, surface):
        self.parent = parent_node
        self.surface = surface
        self.font = pygame.font.SysFont(None, 12)

    def draw(self):
        # Recursively draw debug info for all PhysicsBodies under parent
        for node in self._walk(self.parent):
            if hasattr(node, "collider") and node.collider:
                self._draw_collider(node)
                self._draw_flags(node)

    def _walk(self, node):
        yield node
        for child in getattr(node, "children", []):
            yield from self._walk(child)

    def _draw_collider(self, body):
        rect = body.collider.get_rect()
        sx, sy = body.collider.get_screen_position()
        debug_surf = pygame.Surface((body.collider.width, body.collider.height), pygame.SRCALPHA)
        debug_surf.fill((0, 255, 0, 50))  # Translucent green overlay
        self.surface.blit(debug_surf, (sx, sy))
        pygame.draw.rect(self.surface, (0, 255, 0), (sx, sy, body.collider.width, body.collider.height), 1)

    def _draw_flags(self, body):
        text_lines = [
            f"on_ground: {body.on_ground}",
            f"hit_ceiling: {body.hit_ceiling}",
            f"hit_wall_L: {body.hit_wall_left}",
            f"hit_wall_R: {body.hit_wall_right}",
            f"vel: ({body.velocity_x:.1f}, {body.velocity_y:.1f})",
        ]
        sx, sy = body.collider.get_screen_position()
        for i, line in enumerate(text_lines):
            text_surf = self.font.render(line, True, (255, 255, 0))
            self.surface.blit(text_surf, (sx + body.collider.width + 2, sy + i*12))
