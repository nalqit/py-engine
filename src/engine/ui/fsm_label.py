from src.engine.scene.node2d import Node2D


class FSMLabel(Node2D):
    def __init__(self, name, body, y_offset=-20):
        super().__init__(name, 0, y_offset)
        self.body = body

    def render(self, surface):
        from src.engine.core.engine import Engine
        renderer = Engine.instance.renderer if Engine.instance else None
        if not renderer:
            super().render(surface)
            return

        state_name = self.body.state_machine.current_state.name
        sx, sy = self.get_screen_position()
        renderer.draw_text(surface, state_name, (255, 255, 255), sx, sy, size=16)

        super().render(surface)
