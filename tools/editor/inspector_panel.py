"""
inspector_panel.py — Property Inspector for the PyEngine2D Editor

Shows editable fields for the currently selected node.
All property edits are pushed through EditorModel.change_property()
so they are fully undoable.

Property sync:
    - Model emits selection_changed → Inspector rebuilds form.
    - Inspector user edits → PropertyChangeCommand → model notifies
      scene_changed → Viewport + Scene Tree update.
    - Inherited properties (Camera2D target, etc.) are shown correctly
      because we inspect the node's actual class attributes.
"""

from __future__ import annotations

from typing import Optional, TYPE_CHECKING

from PyQt5.QtWidgets import (
    QDockWidget, QWidget, QVBoxLayout, QFormLayout,
    QLineEdit, QDoubleSpinBox, QSpinBox, QCheckBox,
    QLabel, QScrollArea, QFrame, QGroupBox,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

import os, sys

_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from src.pyengine2D.scene.node import Node
from src.pyengine2D.scene.node2d import Node2D

if TYPE_CHECKING:
    from tools.editor.editor_model import EditorModel


class InspectorPanel(QDockWidget):
    """Dockable property inspector panel."""

    def __init__(self, model: "EditorModel", parent=None):
        super().__init__("Inspector", parent)
        self.model = model
        self.setMinimumWidth(260)
        self.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)

        # Scroll area for long property lists
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        self._form_container = QWidget()
        self._form_layout = QVBoxLayout(self._form_container)
        self._form_layout.setAlignment(Qt.AlignTop)
        self._form_layout.setContentsMargins(8, 8, 8, 8)
        scroll.setWidget(self._form_container)
        self.setWidget(scroll)

        self._updating = False  # prevent re-entrant edits

        # Listen to model
        self.model.on_selection_changed(self._rebuild)
        self.model.on_scene_changed(self._rebuild)

    # ──────────────────────────────────────────────────────────────────
    # Rebuild form for current selection
    # ──────────────────────────────────────────────────────────────────

    def _rebuild(self):
        self._updating = True
        # Clear existing widgets
        while self._form_layout.count():
            item = self._form_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        node = self.model.selected_node
        if node is None:
            lbl = QLabel("No node selected")
            lbl.setStyleSheet("color: #888; font-style: italic; padding: 20px;")
            self._form_layout.addWidget(lbl)
            self._updating = False
            return

        # ── Header ──
        header = QLabel(f"🔧 {type(node).__name__}")
        header.setFont(QFont("Segoe UI", 12, QFont.Bold))
        header.setStyleSheet("color: #4FC3F7; padding: 4px 0;")
        self._form_layout.addWidget(header)

        # ── Name ──
        self._add_string_field("name", "Name", node.name, node)

        # ── Node2D properties ──
        if isinstance(node, Node2D):
            group = QGroupBox("Transform")
            group.setStyleSheet("QGroupBox { font-weight: bold; }")
            form = QFormLayout()
            form.setContentsMargins(8, 16, 8, 8)

            self._add_float_to_form(form, "local_x", "X", node.local_x, node, -99999, 99999)
            self._add_float_to_form(form, "local_y", "Y", node.local_y, node, -99999, 99999)
            self._add_float_to_form(form, "scale_x", "Scale X", node.scale_x, node, 0.01, 100)
            self._add_float_to_form(form, "scale_y", "Scale Y", node.scale_y, node, 0.01, 100)
            self._add_float_to_form(form, "rotation", "Rotation", node.rotation, node, -360, 360)

            group.setLayout(form)
            self._form_layout.addWidget(group)

            # visible & z_index
            group2 = QGroupBox("Rendering")
            group2.setStyleSheet("QGroupBox { font-weight: bold; }")
            form2 = QFormLayout()
            form2.setContentsMargins(8, 16, 8, 8)
            self._add_bool_to_form(form2, "visible", "Visible", 
                                   getattr(node, "visible", True), node)
            self._add_int_to_form(form2, "z_index", "Z Index",
                                  getattr(node, "z_index", 0), node, -100, 1000)
            group2.setLayout(form2)
            self._form_layout.addWidget(group2)

        # ── SpriteNode extras ──
        if hasattr(node, "_image_path"):
            group = QGroupBox("Sprite")
            form = QFormLayout()
            form.setContentsMargins(8, 16, 8, 8)
            self._add_string_field_form(form, "_image_path", "Image Path",
                                        getattr(node, "_image_path", ""), node)
            self._add_bool_to_form(form, "centered", "Centered",
                                   getattr(node, "centered", False), node)
            group.setLayout(form)
            self._form_layout.addWidget(group)

        # ── RectangleNode/CircleNode extras ──
        if hasattr(node, "radius"):
            group = QGroupBox("Circle")
            form = QFormLayout()
            form.setContentsMargins(8, 16, 8, 8)
            self._add_float_to_form(form, "radius", "Radius",
                                    getattr(node, "radius", 0), node, 0, 9999)
            group.setLayout(form)
            self._form_layout.addWidget(group)

        if hasattr(node, "width") and hasattr(node, "height") and not hasattr(node, "radius"):
            group = QGroupBox("Rectangle")
            form = QFormLayout()
            form.setContentsMargins(8, 16, 8, 8)
            self._add_float_to_form(form, "width", "Width",
                                    getattr(node, "width", 0), node, 0, 9999)
            self._add_float_to_form(form, "height", "Height",
                                    getattr(node, "height", 0), node, 0, 9999)
            group.setLayout(form)
            self._form_layout.addWidget(group)

        self._form_layout.addStretch()
        self._updating = False

    # ──────────────────────────────────────────────────────────────────
    # Widget builders
    # ──────────────────────────────────────────────────────────────────

    def _add_string_field(self, prop_name, label_text, value, node):
        form = QFormLayout()
        self._add_string_field_form(form, prop_name, label_text, value, node)
        wrapper = QWidget()
        wrapper.setLayout(form)
        self._form_layout.addWidget(wrapper)

    def _add_string_field_form(self, form, prop_name, label_text, value, node):
        edit = QLineEdit(str(value))
        edit.setStyleSheet("padding: 4px; border: 1px solid #555; border-radius: 3px;")
        old_val = value

        def on_edit():
            if self._updating:
                return
            new_val = edit.text()
            if new_val != old_val:
                self.model.change_property(node, prop_name, old_val, new_val)

        edit.editingFinished.connect(on_edit)
        form.addRow(label_text + ":", edit)

    def _add_float_to_form(self, form, prop_name, label_text, value, node,
                            min_val=-99999, max_val=99999):
        spin = QDoubleSpinBox()
        spin.setRange(min_val, max_val)
        spin.setDecimals(2)
        spin.setSingleStep(1.0)
        spin.setValue(value)
        spin.setStyleSheet("padding: 2px;")

        old_val = value

        def on_change(new_val):
            if self._updating:
                return
            nonlocal old_val
            if new_val != old_val:
                self.model.change_property(node, prop_name, old_val, new_val)
                old_val = new_val

        spin.valueChanged.connect(on_change)
        form.addRow(label_text + ":", spin)

    def _add_int_to_form(self, form, prop_name, label_text, value, node,
                          min_val=0, max_val=1000):
        spin = QSpinBox()
        spin.setRange(min_val, max_val)
        spin.setValue(int(value))
        spin.setStyleSheet("padding: 2px;")

        old_val = int(value)

        def on_change(new_val):
            if self._updating:
                return
            nonlocal old_val
            if new_val != old_val:
                self.model.change_property(node, prop_name, old_val, new_val)
                old_val = new_val

        spin.valueChanged.connect(on_change)
        form.addRow(label_text + ":", spin)

    def _add_bool_to_form(self, form, prop_name, label_text, value, node):
        cb = QCheckBox()
        cb.setChecked(bool(value))

        old_val = bool(value)

        def on_change(state):
            if self._updating:
                return
            nonlocal old_val
            new_val = bool(state)
            if new_val != old_val:
                self.model.change_property(node, prop_name, old_val, new_val)
                old_val = new_val

        cb.stateChanged.connect(on_change)
        form.addRow(label_text + ":", cb)
