import time
import tracemalloc

class EngineProfiler:
    """Per-subsystem timing + delta spike detection + memory tracking + resource counters."""
    def __init__(self):
        self.timings = {}
        self.spike_log = []
        self.frame_count = 0
        self.spike_threshold = 0.025  # 25ms = below 40fps
        self._starts = {}
        self._resource_counters = {}  # name -> value
        self._tracemalloc_started = False

    def begin(self, subsystem: str):
        self._starts[subsystem] = time.perf_counter()

    def end(self, subsystem: str):
        if subsystem in self._starts:
            self.timings[subsystem] = (time.perf_counter() - self._starts[subsystem]) * 1000

    def log_frame(self, dt: float):
        self.frame_count += 1
        if dt > self.spike_threshold:
            self.spike_log.append((self.frame_count, dt))

    # ------------------------------------------------------------------
    # Resource tracking (lightweight counters for pools, particles, etc.)
    # ------------------------------------------------------------------

    def track(self, name: str, value):
        """Record a named resource counter. Call each frame for live tracking."""
        self._resource_counters[name] = value

    def get_tracked(self, name: str, default=0):
        """Read a tracked resource counter."""
        return self._resource_counters.get(name, default)

    # ------------------------------------------------------------------
    # Memory
    # ------------------------------------------------------------------

    def get_memory_mb(self) -> float:
        """
        Returns current traced memory in MB using tracemalloc.
        Much cheaper than iterating gc.get_objects().
        """
        if not self._tracemalloc_started:
            tracemalloc.start()
            self._tracemalloc_started = True
        current, _ = tracemalloc.get_traced_memory()
        return current / (1024 * 1024)

    # ------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------

    def print_summary(self):
        print("\n=== Engine Profiler Summary ===")
        print(f"Total Frames: {self.frame_count}")
        print(f"Frame Spikes (> {self.spike_threshold*1000}ms): {len(self.spike_log)}")
        if self.spike_log:
            worst_spike = max(self.spike_log, key=lambda x: x[1])
            print(f"  Worst Spike: {worst_spike[1]*1000:.2f}ms on frame {worst_spike[0]}")
        print(f"Est. Engine Memory: {self.get_memory_mb():.2f} MB")
        if self._resource_counters:
            print("Resource Counters:")
            for k, v in self._resource_counters.items():
                print(f"  {k}: {v}")
        print("Final Recorded Subsystem Timings:")
        for k, v in self.timings.items():
            print(f"  {k}: {v:.3f}ms")
        print("===============================\n")
