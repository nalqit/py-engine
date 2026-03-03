from src.pyengine2D.scene.node2d import Node2D


class DebugDraw:
    def __init__(self, parent_node, surface):
        self.parent = parent_node
        self.surface = surface

    def draw(self):
        from src.pyengine2D.core.engine import Engine
        if not Engine.instance or not Engine.instance.debug_mode:
            return
            
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
        from src.pyengine2D.core.engine import Engine
        renderer = Engine.instance.renderer if Engine.instance else None
        if not renderer:
            return

        sx, sy = body.collider.get_screen_position()
        w = int(body.collider.width)
        h = int(body.collider.height)

        # Translucent green overlay
        debug_surf = renderer.create_surface(w, h, alpha=True)
        renderer.fill(debug_surf, (0, 255, 0, 50))
        renderer.blit(self.surface, debug_surf, (int(sx), int(sy)))
        renderer.draw_rect(self.surface, (0, 255, 0), sx, sy, w, h, 1)

    def _draw_flags(self, body):
        from src.pyengine2D.core.engine import Engine
        renderer = Engine.instance.renderer if Engine.instance else None
        if not renderer:
            return

        text_lines = [
            f"vel: ({body.velocity_x:.1f}, {body.velocity_y:.1f})",
            f"gravity: {body.use_gravity}",
            f"pushable: {body.pushable}",
        ]
        sx, sy = body.collider.get_screen_position()
        for i, line in enumerate(text_lines):
            renderer.draw_text(self.surface, line, (255, 255, 0),
                               sx + body.collider.width + 2, sy + i * 12, size=12)
