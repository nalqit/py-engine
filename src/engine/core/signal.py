"""
Engine Signal System — Phase 1

A lightweight observer-pattern implementation for decoupled communication
between engine subsystems and game logic.

Usage:
    signal = Signal("on_damage")
    signal.connect(my_handler)
    signal.emit(amount=10, source=enemy)
    signal.disconnect(my_handler)
"""


class Signal:
    """
    A named signal that notifies connected listeners when emitted.

    Thread-safety: NOT required (single-threaded engine).
    Memory safety: Call disconnect() or disconnect_all() when the owner is removed.
    """

    __slots__ = ('name', '_listeners')

    def __init__(self, name: str = ""):
        self.name = name
        self._listeners = []

    def connect(self, callback) -> None:
        """
        Subscribe a callback to this signal.
        Silently ignores duplicates.
        """
        if callback not in self._listeners:
            self._listeners.append(callback)

    def disconnect(self, callback) -> None:
        """
        Unsubscribe a callback from this signal.
        Silently ignores if not connected.
        """
        try:
            self._listeners.remove(callback)
        except ValueError:
            pass

    def disconnect_all(self) -> None:
        """Remove all listeners."""
        self._listeners.clear()

    def emit(self, *args, **kwargs) -> None:
        """
        Notify all connected listeners.
        Listeners are called in connection order.
        A snapshot of the listener list is used so that connect/disconnect
        during emission is safe.
        """
        for callback in self._listeners[:]:  # Iterate over a copy
            callback(*args, **kwargs)

    @property
    def listener_count(self) -> int:
        """Number of currently connected listeners."""
        return len(self._listeners)

    def __repr__(self):
        return f"Signal({self.name!r}, listeners={self.listener_count})"


class SignalMixin:
    """
    Mixin that adds signal management to any class.
    
    Provides:
        - register_signal(name): create a named signal
        - get_signal(name): retrieve a signal by name
        - emit_signal(name, *args, **kwargs): emit a signal by name
        - disconnect_all_signals(): cleanup all signals (call on destruction)
    
    Usage:
        class MyNode(Node, SignalMixin):
            def __init__(self):
                super().__init__("MyNode")
                self.register_signal("on_health_changed")
                self.register_signal("on_died")
            
            def take_damage(self, amount):
                self.health -= amount
                self.emit_signal("on_health_changed", self.health)
                if self.health <= 0:
                    self.emit_signal("on_died")
    """

    def register_signal(self, name: str) -> Signal:
        """Create and register a named signal."""
        if not hasattr(self, '_signals'):
            self._signals = {}
        if name not in self._signals:
            self._signals[name] = Signal(name)
        return self._signals[name]

    def get_signal(self, name: str) -> Signal:
        """
        Retrieve a registered signal by name.
        Raises KeyError if not registered.
        """
        if not hasattr(self, '_signals') or name not in self._signals:
            raise KeyError(f"Signal '{name}' not registered on {self!r}")
        return self._signals[name]

    def emit_signal(self, name: str, *args, **kwargs) -> None:
        """Emit a registered signal by name. No-op if signal doesn't exist."""
        if hasattr(self, '_signals') and name in self._signals:
            self._signals[name].emit(*args, **kwargs)

    def disconnect_all_signals(self) -> None:
        """Disconnect all listeners from all signals on this object."""
        if hasattr(self, '_signals'):
            for signal in self._signals.values():
                signal.disconnect_all()
