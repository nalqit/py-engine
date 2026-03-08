"""
viewport_widget.py — Pygame-based Scene Viewport for the Editor

Embeds a Pygame rendering surface inside a QWidget.
Provides:
    - Editor camera with pan (middle-drag) & zoom (scroll wheel)
    - Node picking (left-click)
    - Node dragging (left-drag on selected node)
    - Selection highlight (orange outline)
    - Optional grid overlay

Thread safety:
    The QTimer fires on the Qt main thread. _render_frame() only *reads*
    the EditorModel (scene_root, selected_node). All writes (move, select)
    flow through EditorModel.push_command() which also runs on the main
    thread, so there are no race conditions.
"""

from __future__ import annotations

import os
import sys
import math
from typing import Optional, TYPE_CHECKING

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QSizePolicy
from PyQt5.QtCore import QTimer, Qt, QSize
from PyQt5.QtGui import QPainter, QImage, QColor

import pygame

_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from src.pyengine2D.scene.node import Node
from src.pyengine2D.scene.node2d import Node2D

if TYPE_CHECKING:
    from tools.editor.editor_model import EditorModel


# ═══════════════════════════════════════════════════════════════════════════
#  Constants
# ═══════════════════════════════════════════════════════════════════════════

_BG_COLOR = (40, 40, 48)
_GRID_COLOR = (60, 60, 70)
_GRID_SIZE = 32
_SELECT_COLOR = (255, 165, 0)  # orange
_HOVER_COLOR = (255, 255, 255, 80)
_AXIS_X_COLOR = (200, 60, 60)
_AXIS_Y_COLOR = (60, 200, 60)
_NODE_PLACEHOLDER_COLOR = (100, 160, 255)
_FPS = 60
_HIT_PADDING = 8  # extra pixels around node for easier clicking


# ═══════════════════════════════════════════════════════════════════════════
#  ViewportWidget
# ═══════════════════════════════════════════════════════════════════════════

class ViewportWidget(QWidget):
    """
    Renders the scene tree using Pygame inside a QWidget via QImage bridge.

    Instead of embedding Pygame via SDL_WINDOWID (which has driver-specific
    issues), we render to a Pygame Surface, then convert to a QImage for
    QPainter blitting. This is portable, flicker-free, and safe.
    """

    def __init__(self, model: "EditorModel", parent=None):
        super().__init__(parent)
        self.model = model
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setMinimumSize(400, 300)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setMouseTracking(True)

        # ── Editor camera state ──
        self.cam_x: float = 0.0
        self.cam_y: float = 0.0
        self.cam_zoom: float = 1.0

        # ── Interaction state ──
        self._is_panning = False
        self._pan_start = (0, 0)
        self._pan_cam_start = (0.0, 0.0)

        self._is_dragging = False
        self._drag_node: Optional[Node2D] = None
        self._drag_start_world = (0.0, 0.0)
        self._drag_node_start = (0.0, 0.0)

        self._hovered_node: Optional[Node2D] = None
        self._show_grid = True

        # ── Pygame surface ──
        self._pg_surface: Optional[pygame.Surface] = None
        self._pg_inited = False

        # ── Render timer (singleShot chain to prevent overlap) ──
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self._on_timer)
        self._timer.start(1000 // _FPS)

    # ──────────────────────────────────────────────────────────────────
    # Pygame init (lazy)
    # ──────────────────────────────────────────────────────────────────

    def _ensure_pg(self):
        if not self._pg_inited:
            if not pygame.get_init():
                os.environ["SDL_VIDEODRIVER"] = "dummy"
                pygame.init()
            self._pg_inited = True
        w, h = max(self.width(), 1), max(self.height(), 1)
        if self._pg_surface is None or self._pg_surface.get_size() != (w, h):
            self._pg_surface = pygame.Surface((w, h))

    # ──────────────────────────────────────────────────────────────────
    # Timer callback — render one frame then re-schedule
    # ──────────────────────────────────────────────────────────────────

    def _on_timer(self):
        self._render_frame()
        self.update()  # schedule Qt repaint
        self._timer.start(1000 // _FPS)

    # ──────────────────────────────────────────────────────────────────
    # Core render
    # ──────────────────────────────────────────────────────────────────

    def _render_frame(self):
        self._ensure_pg()
        surf = self._pg_surface
        w, h = surf.get_size()
        surf.fill(_BG_COLOR)

        # ── Grid ──
        if self._show_grid:
            self._draw_grid(surf, w, h)

        # ── World axes ──
        self._draw_axes(surf, w, h)

        # ── Draw scene nodes ──
        if self.model.scene_root:
            self._draw_node_recursive(surf, self.model.scene_root, w, h)

        # ── Selection highlight ──
        sel = self.model.selected_node
        if sel and isinstance(sel, Node2D):
            self._draw_selection(surf, sel, w, h)

    def _draw_grid(self, surf, w, h):
        scaled_grid = max(1, int(_GRID_SIZE * self.cam_zoom))
        # Calculate start offset
        offset_x = (-self.cam_x * self.cam_zoom + w / 2) % scaled_grid
        offset_y = (-self.cam_y * self.cam_zoom + h / 2) % scaled_grid
        for x in range(int(offset_x), w, scaled_grid):
            pygame.draw.line(surf, _GRID_COLOR, (x, 0), (x, h), 1)
        for y in range(int(offset_y), h, scaled_grid):
            pygame.draw.line(surf, _GRID_COLOR, (0, y), (w, y), 1)

    def _draw_axes(self, surf, w, h):
        ox = int(-self.cam_x * self.cam_zoom + w / 2)
        oy = int(-self.cam_y * self.cam_zoom + h / 2)
        if 0 <= ox < w:
            pygame.draw.line(surf, _AXIS_Y_COLOR, (ox, 0), (ox, h), 2)
        if 0 <= oy < h:
            pygame.draw.line(surf, _AXIS_X_COLOR, (0, oy), (w, oy), 2)

    def _draw_node_recursive(self, surf, node, w, h):
        if isinstance(node, Node2D):
            sx, sy = self._world_to_screen(node.local_x, node.local_y, w, h)
            # Draw a node placeholder box
            nw = int(getattr(node, "width", 0) or 32)
            nh = int(getattr(node, "height", 0) or 32)
            radius = int(getattr(node, "radius", 0) or 0)
            sw = int(nw * self.cam_zoom)
            sh = int(nh * self.cam_zoom)

            if radius > 0:
                pygame.draw.circle(surf, _NODE_PLACEHOLDER_COLOR,
                                   (int(sx), int(sy)),
                                   int(radius * self.cam_zoom), 2)
            else:
                rect = pygame.Rect(int(sx), int(sy), max(sw, 4), max(sh, 4))
                pygame.draw.rect(surf, _NODE_PLACEHOLDER_COLOR, rect, 2)

            # Node name label
            if pygame.font.get_init():
                font = pygame.font.SysFont("Arial", max(9, int(11 * self.cam_zoom)))
                label = font.render(node.name, True, (220, 220, 220))
                surf.blit(label, (int(sx), int(sy) - int(14 * self.cam_zoom)))

        for child in node.children:
            self._draw_node_recursive(surf, child, w, h)

    def _draw_selection(self, surf, node: Node2D, w, h):
        sx, sy = self._world_to_screen(node.local_x, node.local_y, w, h)
        nw = int(getattr(node, "width", 0) or 32)
        nh = int(getattr(node, "height", 0) or 32)
        sw = int(nw * self.cam_zoom)
        sh = int(nh * self.cam_zoom)
        pad = 3
        rect = pygame.Rect(int(sx) - pad, int(sy) - pad,
                           max(sw, 4) + pad * 2, max(sh, 4) + pad * 2)
        pygame.draw.rect(surf, _SELECT_COLOR, rect, 2)
        # Corner handles
        for cx, cy in [(rect.left, rect.top), (rect.right, rect.top),
                       (rect.left, rect.bottom), (rect.right, rect.bottom)]:
            pygame.draw.rect(surf, _SELECT_COLOR, (cx - 3, cy - 3, 6, 6))

    # ──────────────────────────────────────────────────────────────────
    # Coordinate math
    # ──────────────────────────────────────────────────────────────────

    def _world_to_screen(self, wx, wy, w, h):
        sx = (wx - self.cam_x) * self.cam_zoom + w / 2
        sy = (wy - self.cam_y) * self.cam_zoom + h / 2
        return sx, sy

    def _screen_to_world(self, sx, sy):
        w, h = self.width(), self.height()
        wx = (sx - w / 2) / self.cam_zoom + self.cam_x
        wy = (sy - h / 2) / self.cam_zoom + self.cam_y
        return wx, wy

    # ──────────────────────────────────────────────────────────────────
    # Hit-testing
    # ──────────────────────────────────────────────────────────────────

    def _hit_test(self, world_x, world_y, node=None) -> Optional[Node2D]:
        """Find the front-most Node2D under (world_x, world_y)."""
        if node is None:
            node = self.model.scene_root
        if node is None:
            return None

        hit = None
        # Check children first (front-most = last child)
        for child in reversed(node.children):
            result = self._hit_test(world_x, world_y, child)
            if result:
                return result

        if isinstance(node, Node2D) and node is not self.model.scene_root:
            nw = getattr(node, "width", 0) or 32
            nh = getattr(node, "height", 0) or 32
            pad = _HIT_PADDING / self.cam_zoom
            if (node.local_x - pad <= world_x <= node.local_x + nw + pad and
                    node.local_y - pad <= world_y <= node.local_y + nh + pad):
                return node
        return hit

    # ──────────────────────────────────────────────────────────────────
    # Qt event handlers
    # ──────────────────────────────────────────────────────────────────

    def paintEvent(self, event):
        if self._pg_surface is None:
            return
        w, h = self._pg_surface.get_size()
        raw = pygame.image.tostring(self._pg_surface, "RGB")
        qimg = QImage(raw, w, h, w * 3, QImage.Format_RGB888)
        painter = QPainter(self)
        painter.drawImage(0, 0, qimg)
        painter.end()

    def resizeEvent(self, event):
        self._pg_surface = None  # force re-create on next render
        super().resizeEvent(event)

    def sizeHint(self):
        return QSize(800, 600)

    # ── Mouse events ──

    def mousePressEvent(self, event):
        if event.button() == Qt.MiddleButton:
            self._is_panning = True
            self._pan_start = (event.x(), event.y())
            self._pan_cam_start = (self.cam_x, self.cam_y)
            self.setCursor(Qt.ClosedHandCursor)
        elif event.button() == Qt.LeftButton:
            wx, wy = self._screen_to_world(event.x(), event.y())
            hit = self._hit_test(wx, wy)
            if hit:
                self.model.select_node(hit)
                # Start dragging
                self._is_dragging = True
                self._drag_node = hit
                self._drag_start_world = (wx, wy)
                self._drag_node_start = (hit.local_x, hit.local_y)
            else:
                self.model.select_node(None)
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._is_panning:
            dx = (event.x() - self._pan_start[0]) / self.cam_zoom
            dy = (event.y() - self._pan_start[1]) / self.cam_zoom
            self.cam_x = self._pan_cam_start[0] - dx
            self.cam_y = self._pan_cam_start[1] - dy
        elif self._is_dragging and self._drag_node:
            wx, wy = self._screen_to_world(event.x(), event.y())
            dx = wx - self._drag_start_world[0]
            dy = wy - self._drag_start_world[1]
            self._drag_node.local_x = self._drag_node_start[0] + dx
            self._drag_node.local_y = self._drag_node_start[1] + dy
        else:
            # Update hover
            wx, wy = self._screen_to_world(event.x(), event.y())
            self._hovered_node = self._hit_test(wx, wy)
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MiddleButton:
            self._is_panning = False
            self.setCursor(Qt.ArrowCursor)
        elif event.button() == Qt.LeftButton and self._is_dragging:
            if self._drag_node:
                new_x = self._drag_node.local_x
                new_y = self._drag_node.local_y
                old_x, old_y = self._drag_node_start
                if (new_x != old_x or new_y != old_y):
                    # Revert to old pos, then push command (which applies new pos)
                    self._drag_node.local_x = old_x
                    self._drag_node.local_y = old_y
                    self.model.move_node(self._drag_node, old_x, old_y, new_x, new_y)
            self._is_dragging = False
            self._drag_node = None
        super().mouseReleaseEvent(event)

    def wheelEvent(self, event):
        delta = event.angleDelta().y()
        if delta > 0:
            self.cam_zoom = min(8.0, self.cam_zoom * 1.1)
        else:
            self.cam_zoom = max(0.1, self.cam_zoom / 1.1)
        super().wheelEvent(event)

    def keyPressEvent(self, event):
        speed = 200 / self.cam_zoom
        if event.key() == Qt.Key_W:
            self.cam_y -= speed * 0.05
        elif event.key() == Qt.Key_S:
            self.cam_y += speed * 0.05
        elif event.key() == Qt.Key_A:
            self.cam_x -= speed * 0.05
        elif event.key() == Qt.Key_D:
            self.cam_x += speed * 0.05
        elif event.key() == Qt.Key_G:
            self._show_grid = not self._show_grid
        else:
            super().keyPressEvent(event)

    def toggle_grid(self, checked: bool):
        """Called from toolbar to toggle grid visibility."""
        self._show_grid = checked
