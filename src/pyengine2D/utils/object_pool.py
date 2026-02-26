class ObjectPool:
    """
    Engine utility for pooling objects to avoid reallocation overhead.
    Particularly useful for projectiles, particles, or transient nodes.
    """
    def __init__(self, factory_func, initial_size=0):
        """
        Args:
            factory_func: A callable that returns a new instance of the object.
            initial_size: Number of objects to pre-allocate.
        """
        self._factory = factory_func
        self._pool = []
        for _ in range(initial_size):
            self._pool.append(self._factory())

    def acquire(self):
        """Get an object from the pool, or create a new one if empty."""
        if self._pool:
            return self._pool.pop()
        return self._factory()

    def release(self, obj):
        """Return an object to the pool."""
        self._pool.append(obj)
