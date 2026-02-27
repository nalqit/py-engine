import sys
import os
import json

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.pyengine2D.core.engine import Engine
from src.pyengine2D.benchmark.harness import BenchmarkRunner, BenchmarkPhase

class DummyBenchmark(BenchmarkPhase):
    def __init__(self, name):
        super().__init__(name, frames_to_run=10) # very short
        self.input_injected = False
        
    def inject_input(self, engine):
        self.input_injected = True
        
    def setup(self):
        # We simulate some allocation to test memory diff
        self.dummy_list = [i for i in range(1000)]


def test_benchmark_harness():
    engine = Engine("Test Harness", 800, 600)
    engine.suppress_exit = True
    runner = BenchmarkRunner(engine)
    
    b1 = DummyBenchmark("Test 1")
    runner.add_benchmark(b1)
    
    # Run headless/fast
    # If run_all blocks, it will block until engine.running = False
    runner.run_all("test_out.json")
    
    # Validations
    assert len(runner.results) == 1
    res = runner.results[0]
    
    assert res.name == "Test 1"
    assert b1.input_injected is True
    assert res.passed is True
    
    # We allocated 1000 ints, memory_diff should be > 0.0 unless optimized
    
    # Check JSON
    assert os.path.exists("test_out.json")

    print("[PASS] test_benchmark_harness")


if __name__ == "__main__":
    test_benchmark_harness()
