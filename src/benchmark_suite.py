import random
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.engine.core.engine import Engine
from src.engine.benchmark.harness import BenchmarkRunner, BenchmarkPhase
from src.engine.scene.node2d import Node2D

class FastDot(Node2D):
    def __init__(self, name, x, y):
        super().__init__(name, x, y)
        self.vx = random.uniform(-100, 100)
        self.vy = random.uniform(-100, 100)
        
    def update(self, dt):
        super().update(dt)
        self.local_x += self.vx * dt
        self.local_y += self.vy * dt
        if self.local_x < 0 or self.local_x > 800: self.vx *= -1
        if self.local_y < 0 or self.local_y > 600: self.vy *= -1
        
    def render(self, surface):
        from src.engine.core.engine import Engine
        rx, ry = self.get_global_position()
        Engine.instance.renderer.draw_rect(surface, (255, 100, 100), rx, ry, 2, 2)


class B01_SpriteStress(BenchmarkPhase):
    def __init__(self):
        super().__init__("Sprite Stress (10k Objects)", frames_to_run=300)
        self.budget_update_ms = 16.0 # 60fps ok for 10k items
        self.budget_render_ms = 16.0
        
    def setup(self):
        # We instantiate 10,000 nodes
        self.container = Node2D("Container")
        self.add_child(self.container)
        for i in range(10000):
            dot = FastDot(f"Dot_{i}", random.randint(0, 800), random.randint(0, 600))
            self.container.add_child(dot)
            

from src.engine.ui.ui_node import UINode, Anchor, SizePolicy
from src.engine.ui.containers import VBoxContainer, HBoxContainer
from src.engine.ui.widgets import UILabel, UIPanel

class B02_DeepUI(BenchmarkPhase):
    def __init__(self):
        super().__init__("Deep UI Layout (Nested)", frames_to_run=100)
        self.budget_update_ms = 8.0 # Layout should be fast
        
    def setup(self):
        main = VBoxContainer("Main")
        main.width = 800
        main.height = 600
        self.add_child(main)
        
        # 10 rows
        for i in range(10):
            row = HBoxContainer(f"Row_{i}")
            row.size_policy_x = SizePolicy.FILL
            row.height = 50
            main.add_child(row)
            
            # 10 columns per row
            for j in range(10):
                cell = VBoxContainer(f"Cell_{j}")
                cell.size_policy_x = SizePolicy.FILL
                cell.size_policy_y = SizePolicy.FILL
                row.add_child(cell)
                
                panel = UIPanel("Bg", 10, 10)
                panel.size_policy_x = SizePolicy.FILL
                panel.size_policy_y = SizePolicy.FILL
                
                label = UILabel("Text", f"{i},{j}")
                label.anchor = Anchor.CENTER
                label.is_layout_container = True
                
                panel.add_child(label)
                cell.add_child(panel)


from src.engine.ui.data_binding import ObservableModel
from src.engine.ui.widgets import UIListView

class B03_VirtualDataList(BenchmarkPhase):
    def __init__(self):
        super().__init__("Virtual List (100k Items)", frames_to_run=300)
        
    def setup(self):
        self.model = ObservableModel()
        # Create 100,000 items
        items = [f"Data Row #{i}" for i in range(100000)]
        self.model.set("items", items)
        
        self.list_view = UIListView("List", width=400, height=500, row_height=30, item_class=UILabel)
        self.list_view.set_items(items)
        self.add_child(self.list_view)
        
    def inject_input(self, engine):
        # Auto scroll down 5 pixels a frame
        self.list_view.scroll(5)


if __name__ == "__main__":
    engine = Engine("PyEngine Benchmark Suite", virtual_w=800, virtual_h=600)
    
    # Disable v-sync behavior for accurate stress testing
    # pygame.time.Clock tick without FPS limit goes as fast as possible
    
    runner = BenchmarkRunner(engine)
    runner.add_benchmark(B01_SpriteStress())
    runner.add_benchmark(B02_DeepUI())
    runner.add_benchmark(B03_VirtualDataList())
    
    print("Beginning Benchmark Suite...")
    runner.run_all("final_benchmarks.json")
