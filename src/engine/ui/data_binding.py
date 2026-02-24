from src.engine.core.signal import SignalMixin

class ObservableModel(SignalMixin):
    """
    Base class for reactive data models.
    Automatically emits 'on_changed' whenever a registered property changes.
    Batches changes to prevent redundant UI updates in a single frame.
    """
    def __init__(self):
        super().__init__()
        self.register_signal("on_changed")
        self._properties = {}
        self._dirty_properties = set()
        
    def get(self, prop_name: str, default=None):
        return self._properties.get(prop_name, default)

    def set(self, prop_name: str, value):
        old_val = self._properties.get(prop_name)
        if old_val != value:
            self._properties[prop_name] = value
            self._dirty_properties.add(prop_name)

    def flush_changes(self):
        """
        Called once per frame by the Engine or SceneManager 
        to emit batched changes.
        """
        if self._dirty_properties:
            # Emit the list of changed properties so listeners know what updated
            changed = list(self._dirty_properties)
            self._dirty_properties.clear()
            self.emit_signal("on_changed", changed)


class DataBinding:
    """
    Connects a UINode property or setter method to an ObservableModel.
    When the model changes, the node updates automatically.
    """
    def __init__(self, node, setter_func, model: ObservableModel, prop_name: str, formatter=lambda x: x):
        self.node = node
        self.setter_func = setter_func
        self.model = model
        self.prop_name = prop_name
        self.formatter = formatter
        
        # Initial sync
        self._sync()
        
        # Connect to model changes
        self._callback = self._on_model_changed
        self.model.get_signal("on_changed").connect(self._callback)

    def _sync(self):
        val = self.model.get(self.prop_name)
        formatted_val = self.formatter(val)
        self.setter_func(formatted_val)

    def _on_model_changed(self, changed_props):
        """Called by the model when it flushes changes."""
        if self.prop_name in changed_props:
            self._sync()

    def unbind(self):
        """Stops listening for changes."""
        self.model.get_signal("on_changed").disconnect(self._callback)

