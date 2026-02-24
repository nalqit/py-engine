from src.engine.scene.node import Node


class StatsHUD(Node):
    def __init__(self, name="StatsHUD"):
        super().__init__(name)

    def render(self, surface) -> None:
        from src.engine.core.engine import Engine
        if not Engine.instance:
            return
            
        r = Engine.instance.renderer
        p = Engine.instance.profiler
        fps = int(Engine.instance.fps)
        
        lines = [
            f"FPS: {fps:d}",
            f"Logic: {p.get_average('Logic'):.2f}ms",
            f"Render: {p.get_average('Render'):.2f}ms",
            f"Frame Time: {p.get_average('Frame'):.2f}ms",
            f"Spikes: {len(p.spike_log)}",
        ]
        
        y = 10
        for line in lines:
            r.draw_text(surface, line, (255, 255, 255), 10, y)
            y += 20
        super().render(surface)

