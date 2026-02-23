import time
import sys
import gc

class EngineProfiler:
    """Per-subsystem timing + delta spike detection + memory tracking."""
    def __init__(self):
        self.timings = {}
        self.spike_log = []
        self.frame_count = 0
        self.spike_threshold = 0.025  # 25ms = below 40fps
        self._starts = {}
        
    def begin(self, subsystem: str):
        self._starts[subsystem] = time.perf_counter()
        
    def end(self, subsystem: str):
        if subsystem in self._starts:
            self.timings[subsystem] = (time.perf_counter() - self._starts[subsystem]) * 1000
        
    def log_frame(self, dt: float):
        self.frame_count += 1
        if dt > self.spike_threshold:
            self.spike_log.append((self.frame_count, dt))
            
    def get_memory_mb(self) -> float:
        """Estimates python object memory in MB. Not equivalent to full process memory, but useful for leak tracking."""
        gc.collect()
        try:
            return sum(sys.getsizeof(o) for o in gc.get_objects()) / (1024*1024)
        except Exception:
            return 0.0

    def print_summary(self):
        print("\n=== Engine Profiler Summary ===")
        print(f"Total Frames: {self.frame_count}")
        print(f"Frame Spikes (> {self.spike_threshold*1000}ms): {len(self.spike_log)}")
        if self.spike_log:
            worst_spike = max(self.spike_log, key=lambda x: x[1])
            print(f"  Worst Spike: {worst_spike[1]*1000:.2f}ms on frame {worst_spike[0]}")
        print(f"Est. Engine Memory: {self.get_memory_mb():.2f} MB")
        print("Final Recorded Subsystem Timings:")
        for k, v in self.timings.items():
            print(f"  {k}: {v:.3f}ms")
        print("===============================\n")
