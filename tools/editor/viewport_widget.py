"""
viewport_widget.py — Pygame-based Scene Viewport for the Editor

Embeds a Pygame rendering surface inside a QWidget.
Provides:
    - Editor camera with pan (middle-drag) & zoom (scroll wheel)
    - Node picking (left-click)
    - Node dragging (left-drag on selected node)
    - Selection highlight (orange outline)
    - Optional grid overlay
    - Per-type node drawing via a registry pattern

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
from typing import Callable, Dict, Optional, Tuple, Type, TYPE_CHECKING

from PyQt5.QtWidgets import QWidget, QSizePolicy
from PyQt5.QtCore import QTimer, Qt, QSize
from PyQt5.QtGui import QPainter, QImage

import pygame

_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from src.pyengine2D.scene.node import Node
from src.pyengine2D.scene.node2d import Node2D
from src.pyengine2D.scene.camera2d import Camera2D

# Optional imports — guarded
try:
    from src.pyengine2D.scene.rectangle_node import RectangleNode
except ImportError:
    RectangleNode = None

try:
    from src.pyengine2D.scene.circle_node import CircleNode
except ImportError:
    CircleNode = None

try:
    from src.pyengine2D.scene.sprite_node import SpriteNode
except ImportError:
    SpriteNode = None

try:
    from src.pyengine2D.scene.animated_sprite import AnimatedSprite
except ImportError:
    AnimatedSprite = None

try:
    from src.pyengine2D.scene.tilemap import TilemapNode
except ImportError:
    TilemapNode = None

try:
    from src.pyengine2D.collision.collider2d import Collider2D
except ImportError:
    Collider2D = None

try:
    from src.pyengine2D.collision.area2d import Area2D
except ImportError:
    Area2D = None

if TYPE_CHECKING:
    from tools.editor.editor_model import EditorModel


# ═══════════════════════════════════════════════════════════════════════════
#  Constants
# ═══════════════════════════════════════════════════════════════════════════

_BG_COLOR = (40, 40, 48)
_GRID_COLOR = (60, 60, 70)
_GRID_SIZE = 32
_SELECT_COLOR = (255, 165, 0)       # orange
_AXIS_X_COLOR = (200, 60, 60)
_AXIS_Y_COLOR = (60, 200, 60)
_FPS = 60
_HIT_PADDING = 8

# Per-type drawing colours (used by drawers)
_COL_NODE2D      = (100, 160, 255)    # blue — generic Node2D
_COL_RECT        = None               # will use node.color
_COL_CIRCLE      = None               # will use node.color
_COL_SPRITE      = (255, 100, 200)    # pink placeholder
_COL_ANIM        = (180, 120, 255)    # purple
_COL_CAMERA      = (255, 220, 80)     # gold
_COL_TILEMAP     = (80, 200, 130)     # green
_COL_COLLIDER    = (0, 230, 120, 120) # green semi-transparent
_COL_FALLBACK    = (100, 160, 255)    # blue fallback


# ═══════════════════════════════════════════════════════════════════════════
#  Node Draw Registry
# ═══════════════════════════════════════════════════════════════════════════

# Registry: maps node class → draw function
# Signature: draw_fn(surf, node, sx, sy, zoom, font) -> (draw_w, draw_h)
#   Returns the screen-pixel width/height used (for selection box)
_DRAW_REGISTRY: Dict[type, Callable] = {}


def register_draw(cls):
    """Decorator to register a drawing function for a node class."""
    def decorator(fn):
        if cls is not None:
            _DRAW_REGISTRY[cls] = fn
        return fn
    return decorator


def get_node_draw_size(node, zoom: float) -> Tuple[float, float]:
    """
    Return the screen-pixel (width, height) for a node, accounting for scale.
    Used by hit-testing and selection drawing.
    """
    sx_scale = getattr(node, "scale_x", 1.0) or 1.0
    sy_scale = getattr(node, "scale_y", 1.0) or 1.0

    radius = getattr(node, "radius", 0) or 0
    if radius > 0:
        r = radius * max(abs(sx_scale), abs(sy_scale)) * zoom
        return r * 2, r * 2

    w = getattr(node, "width", 0) or 0
    h = getattr(node, "height", 0) or 0

    # AnimatedSprite uses frame_width/frame_height
    if w == 0:
        w = getattr(node, "frame_width", 0) or 0
    if h == 0:
        h = getattr(node, "frame_height", 0) or 0

    if w == 0 and h == 0:
        w, h = 32, 32  # fallback

    return abs(w * sx_scale * zoom), abs(h * sy_scale * zoom)


# ─── Drawer implementations ──────────────────────────────────────────────

@register_draw(Node2D)
def _draw_node2d(surf, node, sx, sy, zoom, font):
    """Generic Node2D — small cross + name label."""
    size = max(3, int(8 * zoom))
    color = _COL_NODE2D
    pygame.draw.line(surf, color, (int(sx) - size, int(sy)), (int(sx) + size, int(sy)), 2)
    pygame.draw.line(surf, color, (int(sx), int(sy) - size), (int(sx), int(sy) + size), 2)
    if font:
        label = font.render(node.name, True, (200, 200, 210))
        surf.blit(label, (int(sx) + size + 2, int(sy) - 6))
    return 32 * zoom, 32 * zoom


@register_draw(Camera2D)
def _draw_camera2d(surf, node, sx, sy, zoom, font):
    """Camera2D — trapezoid/camera icon in gold."""
    s = max(6, int(16 * zoom))
    color = _COL_CAMERA
    # Camera body (rectangle)
    body = pygame.Rect(int(sx) - s, int(sy) - int(s * 0.6), s * 2, int(s * 1.2))
    pygame.draw.rect(surf, color, body, 2)
    # Lens (small triangle on right)
    lens_pts = [
        (int(sx) + s, int(sy) - int(s * 0.3)),
        (int(sx) + s + int(s * 0.5), int(sy)),
        (int(sx) + s, int(sy) + int(s * 0.3)),
    ]
    pygame.draw.polygon(surf, color, lens_pts, 2)
    if font:
        label = font.render(f"📷 {node.name}", True, _COL_CAMERA)
        surf.blit(label, (int(sx) - s, int(sy) - int(s * 0.6) - int(14 * zoom)))
    return s * 2, int(s * 1.2)


if RectangleNode is not None:
    @register_draw(RectangleNode)
    def _draw_rectangle(surf, node, sx, sy, zoom, font):
        """RectangleNode — filled rect with node.color, scaled."""
        sx_scale = getattr(node, "scale_x", 1.0) or 1.0
        sy_scale = getattr(node, "scale_y", 1.0) or 1.0
        w = int((getattr(node, "width", 32) or 32) * sx_scale * zoom)
        h = int((getattr(node, "height", 32) or 32) * sy_scale * zoom)
        color = getattr(node, "color", (180, 180, 200))
        if isinstance(color, (list, tuple)) and len(color) >= 3:
            draw_color = tuple(color[:3])
        else:
            draw_color = (180, 180, 200)
        rect = pygame.Rect(int(sx), int(sy), max(w, 2), max(h, 2))
        # Semi-transparent fill
        fill_surf = pygame.Surface((rect.w, rect.h), pygame.SRCALPHA)
        fill_surf.fill((*draw_color, 80))
        surf.blit(fill_surf, rect.topleft)
        pygame.draw.rect(surf, draw_color, rect, 2)
        if font:
            label = font.render(node.name, True, (220, 220, 220))
            surf.blit(label, (int(sx), int(sy) - int(14 * zoom)))
        return w, h


if CircleNode is not None:
    @register_draw(CircleNode)
    def _draw_circle(surf, node, sx, sy, zoom, font):
        """CircleNode — true circle with node.color, scaled radius."""
        sx_scale = getattr(node, "scale_x", 1.0) or 1.0
        sy_scale = getattr(node, "scale_y", 1.0) or 1.0
        radius = getattr(node, "radius", 16) or 16
        r = int(radius * max(abs(sx_scale), abs(sy_scale)) * zoom)
        color = getattr(node, "color", (200, 100, 100))
        if isinstance(color, (list, tuple)) and len(color) >= 3:
            draw_color = tuple(color[:3])
        else:
            draw_color = (200, 100, 100)
        center = (int(sx), int(sy))
        # Semi-transparent fill
        if r > 0:
            circle_surf = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
            pygame.draw.circle(circle_surf, (*draw_color, 60), (r, r), r)
            pygame.draw.circle(circle_surf, draw_color, (r, r), r, 2)
            surf.blit(circle_surf, (center[0] - r, center[1] - r))
        if font:
            label = font.render(node.name, True, (220, 220, 220))
            surf.blit(label, (int(sx) + r + 4, int(sy) - 6))
        return r * 2, r * 2


if SpriteNode is not None:
    @register_draw(SpriteNode)
    def _draw_sprite(surf, node, sx, sy, zoom, font):
        """SpriteNode — scaled texture or pink placeholder."""
        sx_scale = getattr(node, "scale_x", 1.0) or 1.0
        sy_scale = getattr(node, "scale_y", 1.0) or 1.0
        raw_w = getattr(node, "width", 0) or 32
        raw_h = getattr(node, "height", 0) or 32
        w = int(raw_w * sx_scale * zoom)
        h = int(raw_h * sy_scale * zoom)

        # Try to render actual texture
        image = getattr(node, "image", None)
        if image is not None and w > 0 and h > 0:
            try:
                scaled = pygame.transform.scale(image, (abs(w), abs(h)))
                draw_x, draw_y = int(sx), int(sy)
                if getattr(node, "centered", False):
                    draw_x -= abs(w) // 2
                    draw_y -= abs(h) // 2
                surf.blit(scaled, (draw_x, draw_y))
                if font:
                    label = font.render(node.name, True, (220, 220, 220))
                    surf.blit(label, (draw_x, draw_y - int(14 * zoom)))
                return abs(w), abs(h)
            except Exception:
                pass

        # Pink placeholder
        rect = pygame.Rect(int(sx), int(sy), max(abs(w), 4), max(abs(h), 4))
        fill = pygame.Surface((rect.w, rect.h), pygame.SRCALPHA)
        fill.fill((*_COL_SPRITE, 60))
        surf.blit(fill, rect.topleft)
        pygame.draw.rect(surf, _COL_SPRITE, rect, 2)
        # Diagonal cross for "missing texture"
        pygame.draw.line(surf, _COL_SPRITE, rect.topleft, rect.bottomright, 1)
        pygame.draw.line(surf, _COL_SPRITE, rect.topright, rect.bottomleft, 1)
        if font:
            label = font.render(f"🖼 {node.name}", True, _COL_SPRITE)
            surf.blit(label, (int(sx), int(sy) - int(14 * zoom)))
        return abs(w), abs(h)


if AnimatedSprite is not None:
    @register_draw(AnimatedSprite)
    def _draw_animated_sprite(surf, node, sx, sy, zoom, font):
        """AnimatedSprite — frame-sized rect in purple."""
        sx_scale = getattr(node, "scale_x", 1.0) or 1.0
        sy_scale = getattr(node, "scale_y", 1.0) or 1.0
        fw = getattr(node, "frame_width", 32) or 32
        fh = getattr(node, "frame_height", 32) or 32
        w = int(fw * sx_scale * zoom)
        h = int(fh * sy_scale * zoom)
        rect = pygame.Rect(int(sx), int(sy), max(w, 4), max(h, 4))
        fill = pygame.Surface((rect.w, rect.h), pygame.SRCALPHA)
        fill.fill((*_COL_ANIM, 50))
        surf.blit(fill, rect.topleft)
        pygame.draw.rect(surf, _COL_ANIM, rect, 2)
        # Film-strip accents
        stripe_h = max(2, int(4 * zoom))
        pygame.draw.rect(surf, _COL_ANIM, (rect.x, rect.y, rect.w, stripe_h))
        pygame.draw.rect(surf, _COL_ANIM, (rect.x, rect.bottom - stripe_h, rect.w, stripe_h))
        if font:
            label = font.render(f"🎞 {node.name}", True, _COL_ANIM)
            surf.blit(label, (int(sx), int(sy) - int(14 * zoom)))
        return w, h


if TilemapNode is not None:
    @register_draw(TilemapNode)
    def _draw_tilemap(surf, node, sx, sy, zoom, font):
        """TilemapNode — dashed bounding rect + label."""
        tw = getattr(node, "tile_width", 32) or 32
        th = getattr(node, "tile_height", 32) or 32
        cols = getattr(node, "map_cols", 0) or 8
        rows = getattr(node, "map_rows", 0) or 6
        w = int(cols * tw * zoom)
        h = int(rows * th * zoom)
        rect = pygame.Rect(int(sx), int(sy), max(w, 4), max(h, 4))
        # Dashed border
        dash = max(4, int(8 * zoom))
        for i in range(0, rect.w, dash * 2):
            pygame.draw.line(surf, _COL_TILEMAP, (rect.x + i, rect.y),
                             (rect.x + min(i + dash, rect.w), rect.y), 2)
            pygame.draw.line(surf, _COL_TILEMAP, (rect.x + i, rect.bottom),
                             (rect.x + min(i + dash, rect.w), rect.bottom), 2)
        for i in range(0, rect.h, dash * 2):
            pygame.draw.line(surf, _COL_TILEMAP, (rect.x, rect.y + i),
                             (rect.x, rect.y + min(i + dash, rect.h)), 2)
            pygame.draw.line(surf, _COL_TILEMAP, (rect.right, rect.y + i),
                             (rect.right, rect.y + min(i + dash, rect.h)), 2)
        if font:
            label = font.render(f"🗺 {node.name} ({cols}x{rows})", True, _COL_TILEMAP)
            surf.blit(label, (int(sx) + 4, int(sy) + 4))
        return w, h


if Collider2D is not None:
    @register_draw(Collider2D)
    def _draw_collider(surf, node, sx, sy, zoom, font):
        """Collider2D — green outlined rect."""
        sx_scale = getattr(node, "scale_x", 1.0) or 1.0
        sy_scale = getattr(node, "scale_y", 1.0) or 1.0
        w = int((getattr(node, "width", 32) or 32) * sx_scale * zoom)
        h = int((getattr(node, "height", 32) or 32) * sy_scale * zoom)
        color = (0, 230, 120)
        rect = pygame.Rect(int(sx), int(sy), max(w, 4), max(h, 4))
        fill = pygame.Surface((rect.w, rect.h), pygame.SRCALPHA)
        fill.fill((*color, 30))
        surf.blit(fill, rect.topleft)
        pygame.draw.rect(surf, color, rect, 1)
        if font:
            lbl = "⬡ " + node.name
            if getattr(node, "is_static", False):
                lbl += " [static]"
            label = font.render(lbl, True, color)
            surf.blit(label, (int(sx), int(sy) - int(12 * zoom)))
        return w, h


def _draw_fallback(surf, node, sx, sy, zoom, font):
    """Fallback for unregistered node types — blue dashed rect."""
    w = int(32 * zoom)
    h = int(32 * zoom)
    color = _COL_FALLBACK
    rect = pygame.Rect(int(sx), int(sy), w, h)
    dash = max(3, int(6 * zoom))
    for i in range(0, w, dash * 2):
        pygame.draw.line(surf, color, (rect.x + i, rect.y),
                         (rect.x + min(i + dash, w), rect.y), 1)
        pygame.draw.line(surf, color, (rect.x + i, rect.bottom),
                         (rect.x + min(i + dash, w), rect.bottom), 1)
    for i in range(0, h, dash * 2):
        pygame.draw.line(surf, color, (rect.x, rect.y + i),
                         (rect.x, rect.y + min(i + dash, h)), 1)
        pygame.draw.line(surf, color, (rect.right, rect.y + i),
                         (rect.right, rect.y + min(i + dash, h)), 1)
    if font:
        type_name = getattr(node, "_original_type", None) or type(node).__name__
        label = font.render(f"? {type_name}: {node.name}", True, color)
        surf.blit(label, (int(sx), int(sy) - int(12 * zoom)))
    return w, h


def _resolve_drawer(node) -> Callable:
    """Find the best drawer for a node, walking the MRO."""
    for cls in type(node).__mro__:
        if cls in _DRAW_REGISTRY:
            return _DRAW_REGISTRY[cls]
    return _draw_fallback


# ═══════════════════════════════════════════════════════════════════════════
#  ViewportWidget
# ═══════════════════════════════════════════════════════════════════════════

class ViewportWidget(QWidget):
    """
    Renders the scene tree using Pygame inside a QWidget via QImage bridge.

    Uses a draw registry pattern so each node type is rendered with its
    correct shape and colour, with proper scale applied.
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
        self._font: Optional[pygame.font.Font] = None

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

    def _get_font(self):
        if self._font is None and pygame.font.get_init():
            self._font = pygame.font.SysFont("Arial", 11)
        return self._font

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

        # ── Draw scene nodes via registry ──
        if self.model.scene_root:
            self._draw_node_recursive(surf, self.model.scene_root, w, h)

        # ── Selection highlight ──
        sel = self.model.selected_node
        if sel and isinstance(sel, Node2D):
            self._draw_selection(surf, sel, w, h)

    def _draw_grid(self, surf, w, h):
        scaled_grid = max(1, int(_GRID_SIZE * self.cam_zoom))
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
        """Recursively draw all nodes using the draw registry."""
        if isinstance(node, Node2D):
            if not getattr(node, "visible", True):
                return  # skip invisible nodes and their children

            sx, sy = self._world_to_screen(node.local_x, node.local_y, w, h)
            drawer = _resolve_drawer(node)
            font = self._get_font()
            drawer(surf, node, sx, sy, self.cam_zoom, font)

        for child in node.children:
            self._draw_node_recursive(surf, child, w, h)

    def _draw_selection(self, surf, node: Node2D, w, h):
        """Draw selection highlight with correct scaled bounds."""
        sx, sy = self._world_to_screen(node.local_x, node.local_y, w, h)
        draw_w, draw_h = get_node_draw_size(node, self.cam_zoom)

        # For circles, adjust origin to top-left of bounding box
        radius = getattr(node, "radius", 0) or 0
        if radius > 0:
            sx -= draw_w / 2
            sy -= draw_h / 2

        pad = 3
        rect = pygame.Rect(
            int(sx) - pad, int(sy) - pad,
            int(draw_w) + pad * 2, int(draw_h) + pad * 2
        )
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
    # Hit-testing (scale-aware)
    # ──────────────────────────────────────────────────────────────────

    def _hit_test(self, world_x, world_y, node=None) -> Optional[Node2D]:
        """Find the front-most Node2D under (world_x, world_y)."""
        if node is None:
            node = self.model.scene_root
        if node is None:
            return None

        # Check children first (front-most = last child drawn)
        for child in reversed(node.children):
            result = self._hit_test(world_x, world_y, child)
            if result:
                return result

        if isinstance(node, Node2D) and node is not self.model.scene_root:
            if not getattr(node, "visible", True):
                return None

            pad = _HIT_PADDING / self.cam_zoom
            sx_scale = getattr(node, "scale_x", 1.0) or 1.0
            sy_scale = getattr(node, "scale_y", 1.0) or 1.0

            radius = getattr(node, "radius", 0) or 0
            if radius > 0:
                # Circle hit test
                r = radius * max(abs(sx_scale), abs(sy_scale))
                dist = math.sqrt((world_x - node.local_x) ** 2 +
                                 (world_y - node.local_y) ** 2)
                if dist <= r + pad:
                    return node
            else:
                nw = getattr(node, "width", 0) or 0
                nh = getattr(node, "height", 0) or 0
                if nw == 0:
                    nw = getattr(node, "frame_width", 0) or 0
                if nh == 0:
                    nh = getattr(node, "frame_height", 0) or 0
                if nw == 0 and nh == 0:
                    nw, nh = 32, 32
                nw *= abs(sx_scale)
                nh *= abs(sy_scale)

                if (node.local_x - pad <= world_x <= node.local_x + nw + pad and
                        node.local_y - pad <= world_y <= node.local_y + nh + pad):
                    return node

        return None

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
        self._pg_surface = None
        self._font = None  # rebuild font on next render
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
                if new_x != old_x or new_y != old_y:
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
