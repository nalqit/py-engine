import json
import tracemalloc
import time
from typing import Dict, Any, List
from src.engine.core.engine import Engine
from src.engine.scene.scene_manager import Scene
import pygame

class BenchmarkResult:
    def __init__(self, name: str):
        self.name = name
        self.passed: bool = True
        self.errors: List[str] = []
        self.avg_fps: float = 0.0
        self.memory_diff_kb: float = 0.0
        self.max_update_ms: float = 0.0
        self.max_render_ms: float = 0.0
        
    def to_dict(self):
        return {
            "name": self.name,
            "passed": self.passed,
            "errors": self.errors,
            "avg_fps": self.avg_fps,
            "memory_diff_kb": self.memory_diff_kb,
            "max_update_ms": self.max_update_ms,
            "max_render_ms": self.max_render_ms
        }

class BenchmarkPhase(Scene):
    """
    A single benchmark scenario.
    Inherits from Scene so it can be managed by SceneManager.
    """
    def __init__(self, name: str, frames_to_run: int = 600):
        super().__init__(name)
        self.frames_to_run = frames_to_run
        self.current_frame = 0
        self.completed = False
        
        # Budgets
        self.budget_update_ms = 8.0 # 120fps physics target
        self.budget_render_ms = 8.0 # 120fps render target
        self.budget_memory_kb = 1024.0 # 1MB leak tolerance
        
        self.result = BenchmarkResult(name)

    def setup(self):
        """Override to build the scene (10,000 sprites, complex UI, etc)"""
        pass

    def inject_input(self, engine: Engine):
        """Override to simulate mouse/keyboard inputs per frame."""
        pass

    def update(self, delta: float):
        if self.completed: return
        super().update(delta)
        
        if self.current_frame >= self.frames_to_run:
            self.completed = True
        self.current_frame += 1


class BenchmarkRunner:
    """
    Executes a suite of BenchmarkPhase scenes automatically.
    Captures memory snapshots, applies synthetic input, and validates budgets.
    """
    def __init__(self, engine: Engine):
        self.engine = engine
        self.benchmarks: List[BenchmarkPhase] = []
        self.results: List[BenchmarkResult] = []
        
        self._current_idx = 0
        self._memory_snapshot1 = None

    def add_benchmark(self, benchmark: BenchmarkPhase):
        self.benchmarks.append(benchmark)

    def run_all(self, output_file: str = "benchmark_results.json"):
        if not self.benchmarks: return
        self.output_file = output_file
        
        # Ensure tracemalloc is running
        if not tracemalloc.is_tracing():
            tracemalloc.start()
            
        print(f"Starting Benchmark Suite: {len(self.benchmarks)} tests")
        
        self._current_idx = 0
        self._start_current_benchmark()
        
        # Hook into Engine.run
        # We will use on_fixed_update and on_render to track frame budgets
        self.engine.run(
            root=None, # Use scene manager
            on_fixed_update=self._on_update,
            on_render=self._on_render
        )
        
        # When engine.run finishes (we call Engine.quit during testing),
        # we write the report. But Engine.quit() calls sys.exit().
        # So we actually need to intercept the end of the suite.

    def _start_current_benchmark(self):
        if self._current_idx >= len(self.benchmarks):
            self._finish_suite()
            return
            
        benchmark = self.benchmarks[self._current_idx]
        print(f"[{benchmark.name}] Setting up...")
        benchmark.setup()
        
        # Force GC to get a clean baseline
        import gc
        gc.collect()
        self._memory_snapshot1 = tracemalloc.take_snapshot()
        
        self.engine.scene_manager.switch_scene(benchmark)
        # Reset profiler for accuracy
        self.engine.profiler.avg_fps = 60.0

    def _finish_current_benchmark(self):
        benchmark = self.benchmarks[self._current_idx]
        
        # Diff memory
        import gc
        gc.collect()
        snapshot2 = tracemalloc.take_snapshot()
        stats = snapshot2.compare_to(self._memory_snapshot1, 'lineno')
        diff_bytes = sum(stat.size_diff for stat in stats)
        benchmark.result.memory_diff_kb = diff_bytes / 1024.0
        
        # Get Frame times
        update_ms = self.engine.profiler.timings.get("Logic", 0)
        render_ms = self.engine.profiler.timings.get("Render", 0)
        
        benchmark.result.max_update_ms = update_ms
        benchmark.result.max_render_ms = render_ms
        benchmark.result.avg_fps = self.engine.profiler.avg_fps
        
        # Validate Budgets
        if benchmark.result.memory_diff_kb > benchmark.budget_memory_kb:
            benchmark.result.passed = False
            benchmark.result.errors.append(f"Memory Diff {benchmark.result.memory_diff_kb:.1f}KB exceeds budget {benchmark.budget_memory_kb}KB")
            
        if update_ms > benchmark.budget_update_ms:
            benchmark.result.passed = False
            benchmark.result.errors.append(f"Update time {update_ms:.1f}ms exceeds budget {benchmark.budget_update_ms}ms")

        if render_ms > benchmark.budget_render_ms:
            benchmark.result.passed = False
            benchmark.result.errors.append(f"Render time {render_ms:.1f}ms exceeds budget {benchmark.budget_render_ms}ms")

        status = "PASS" if benchmark.result.passed else "FAIL"
        print(f"[{benchmark.name}] {status} - FPS: {benchmark.result.avg_fps:.1f} - Mem Diff: {benchmark.result.memory_diff_kb:.1f}KB")
        for err in benchmark.result.errors:
            print(f"  > {err}")
            
        self.results.append(benchmark.result)
        
        self._current_idx += 1
        self._start_current_benchmark()

    def _on_update(self, engine, root, dt):
        if not hasattr(root, "completed"): return # Not a benchmark scene
        
        if root.completed and not getattr(root, "_already_finished", False):
            root._already_finished = True
            self._finish_current_benchmark()
        elif not getattr(root, "_already_finished", False):
            root.inject_input(engine)

    def _on_render(self, engine, root, surface):
        pass

    def _finish_suite(self):
        print("\n=== Benchmark Suite Complete ===")
        report = [res.to_dict() for res in self.results]
        
        # Write to Output file
        out_file = getattr(self, "output_file", "benchmark_results.json")
        with open(out_file, "w") as f:
            json.dump(report, f, indent=4)
            
        print(f"Results written to {out_file}")
        
        # Auto-quit gracefully without sys.exit if running tests
        self.engine.running = False
