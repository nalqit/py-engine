class ObjectPool:
    """
    Engine utility for pooling objects to avoid reallocation overhead.
    Particularly useful for projectiles, particles, or transient nodes.

    Features:
        - Optional reset callback invoked on acquire() for proper object reuse.
        - Optional max_size to cap pool growth and prevent unbounded memory.
        - stats() method returning dict with pool_size, total_acquired, total_released.
    """

    def __init__(self, factory_func, initial_size=0, reset_func=None, max_size=None):
        """
        Args:
            factory_func: A callable that returns a new instance of the object.
            initial_size: Number of objects to pre-allocate.
            reset_func: Optional callable(obj) invoked on each acquired object
                        to reset it to a clean state before reuse.
            max_size: Optional maximum number of objects to keep in the pool.
                      Excess released objects are discarded when pool is full.
        """
        self._factory = factory_func
        self._reset_func = reset_func
        self._max_size = max_size
        self._pool = []
        self._total_acquired = 0
        self._total_released = 0
        for _ in range(initial_size):
            self._pool.append(self._factory())

    def acquire(self):
        """Get an object from the pool, or create a new one if empty."""
        if self._pool:
            obj = self._pool.pop()
        else:
            obj = self._factory()
        if self._reset_func:
            self._reset_func(obj)
        self._total_acquired += 1
        return obj

    def release(self, obj):
        """Return an object to the pool (respects max_size cap)."""
        if self._max_size is not None and len(self._pool) >= self._max_size:
            return  # discard — pool is at capacity
        self._pool.append(obj)
        self._total_released += 1

    def stats(self):
        """Returns a dict with pool diagnostics."""
        return {
            'pool_size': len(self._pool),
            'total_acquired': self._total_acquired,
            'total_released': self._total_released,
        }
