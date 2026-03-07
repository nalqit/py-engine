"""
renderer2d.py — High-level scene renderer for PyEngine2D.

Traverses the Node2D scene tree, applies frustum culling via Camera2D,
respects the Dirty Transform System, sorts by z_index, delegates to each
node's native render(), and optionally draws debug overlays.

Usage::

    from src.pyengine2D.rendering.renderer2d import Renderer2D

    renderer2d = Renderer2D(camera)

    # Inside your game loop (or via engine.run on_render callback)
    renderer2d.draw(root_node, surface)
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING, List, Optional

import pygame

if TYPE_CHECKING:
    from src.pyengine2D.core.engine import Engine

from src.pyengine2D.scene.node import Node
from src.pyengine2D.scene.node2d import Node2D
from src.pyengine2D.scene.camera2d import Camera2D

# ---------------------------------------------------------------------------
# Optional imports — guarded so the module loads even if pieces are missing
# ---------------------------------------------------------------------------
try:
    from src.pyengine2D.scene.tilemap import TilemapNode
except ImportError:  # pragma: no cover
    TilemapNode = None  # type: ignore[misc,assignment]

try:
    from src.pyengine2D.scene.sprite_node import SpriteNode
except ImportError:  # pragma: no cover
    SpriteNode = None  # type: ignore[misc,assignment]

try:
    from src.pyengine2D.scene.animated_sprite import AnimatedSprite
except ImportError:  # pragma: no cover
    AnimatedSprite = None  # type: ignore[misc,assignment]

try:
    from src.pyengine2D.collision.collider2d import Collider2D
except ImportError:  # pragma: no cover
    Collider2D = None  # type: ignore[misc,assignment]

try:
    from src.pyengine2D.scene.particles import ParticleEmitter2D
except ImportError:  # pragma: no cover
    ParticleEmitter2D = None  # type: ignore[misc,assignment]


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
DEFAULT_CULLING_PADDING = 128   # pixels added around the camera rect

# Debug colours
_CLR_BBOX       = (0, 255, 0)
_CLR_COLLIDER   = (255, 80, 80)
_CLR_NAME       = (255, 255, 0)
_CLR_HUD_BG     = (0, 0, 0, 180)
_CLR_HUD_TEXT   = (255, 255, 255)


# ═══════════════════════════════════════════════════════════════════════════
#  Renderer2D
# ═══════════════════════════════════════════════════════════════════════════

class Renderer2D:
    """
    Scene-aware 2D renderer.

    Parameters
    ----------
    camera : Camera2D
        Camera whose viewport drives frustum culling.
    debug_mode : bool
        Draw bounding boxes, node names, collision shapes, FPS & node count.
    culling_padding : int
        Extra pixel margin around the viewport for culling tolerance.
    """

    def __init__(
        self,
        camera: Camera2D,
        *,
        debug_mode: bool = False,
        culling_padding: int = DEFAULT_CULLING_PADDING,
    ) -> None:
        self.camera = camera
        self.debug_mode = debug_mode
        self.culling_padding = culling_padding

        # --- internal stats ---
        self._frame_count: int = 0
        self._fps: float = 0.0
        self._last_fps_time: float = time.perf_counter()
        self._rendered_count: int = 0
        self._total_count: int = 0

        # --- lazy font cache ---
        self._font: Optional[pygame.font.Font] = None
        self._small_font: Optional[pygame.font.Font] = None

    # ==================================================================
    # Public API
    # ==================================================================

    def draw(
        self,
        root: Node,
        surface: pygame.Surface,
        engine: Optional["Engine"] = None,
    ) -> None:
        """
        Traverse *root*, cull, sort, render, and optionally overlay debug info.

        Parameters
        ----------
        root : Node | Node2D
            Scene-tree root.
        surface : pygame.Surface
            Render target (usually ``engine.game_surface``).
        engine : Engine, optional
            Passed through for FPS readout; not required.
        """
        screen_w, screen_h = surface.get_size()

        # 1 ── resolve dirty transforms once from root downward
        if hasattr(root, "update_transforms"):
            root.update_transforms()

        # 2 ── build the camera viewport rect (world-space)
        viewport = self._build_viewport(screen_w, screen_h)

        # 3 ── gather visible, on-screen Node2D instances
        gathered: List[Node2D] = []
        self._total_count = 0
        self._gather(root, viewport, gathered)

        # 4 ── depth-sort by z_index (stable → preserves tree order for ties)
        gathered.sort(key=_z_sort_key)

        # 5 ── render every gathered node via its own render()
        self._rendered_count = len(gathered)
        for node in gathered:
            node.render(surface)

        # 6 ── debug overlays
        if self.debug_mode:
            self._overlay_debug(gathered, surface)
            self._overlay_hud(surface, screen_w, screen_h, engine)

        # 7 ── tick internal FPS counter
        self._tick_fps()

    # ==================================================================
    # Tree traversal
    # ==================================================================

    def _gather(
        self,
        node: Node,
        viewport: pygame.Rect,
        out: List[Node2D],
    ) -> None:
        """Recursively collect renderable Node2D instances."""
        self._total_count += 1

        # Skip invisible nodes (attribute defaults to True when absent)
        if not getattr(node, "visible", True):
            return

        if isinstance(node, Node2D):
            # Tilemaps & particle emitters manage their own internal culling,
            # so always include them (they skip off-screen chunks/particles
            # inside their render()).
            if _always_include(node):
                out.append(node)
            elif self._in_viewport(node, viewport):
                out.append(node)
            # Even if this node is culled its children may still be visible
            # (e.g. a container at 0,0 with children far away).

        for child in node.children:
            self._gather(child, viewport, out)

    # ==================================================================
    # Frustum culling
    # ==================================================================

    def _build_viewport(self, screen_w: int, screen_h: int) -> pygame.Rect:
        """World-space rect of what the camera can see, plus padding."""
        if self.camera is not None:
            gx, gy = self.camera.get_global_position()
        else:
            gx, gy = 0.0, 0.0
        pad = self.culling_padding
        return pygame.Rect(
            int(gx) - screen_w // 2 - pad,
            int(gy) - screen_h // 2 - pad,
            screen_w + pad * 2,
            screen_h + pad * 2,
        )

    @staticmethod
    def _in_viewport(node: Node2D, viewport: pygame.Rect) -> bool:
        """Check whether *node*'s bounding rect overlaps the viewport."""
        gx, gy = node.get_global_position()

        # --- determine bounding width / height ---
        w = getattr(node, "width", 0) or 0
        h = getattr(node, "height", 0) or 0

        # AnimatedSprite stores frame_width / frame_height
        if w == 0:
            w = getattr(node, "frame_width", 0) or 0
        if h == 0:
            h = getattr(node, "frame_height", 0) or 0

        # CircleNode → use diameter
        radius = getattr(node, "radius", 0) or 0
        if radius and w == 0 and h == 0:
            w = h = radius * 2
            gx -= radius
            gy -= radius

        # Apply node scale
        sx = getattr(node, "scale_x", 1.0) or 1.0
        sy = getattr(node, "scale_y", 1.0) or 1.0
        w = int(w * sx)
        h = int(h * sy)

        # No size info → assume logical / container node → always include
        if w <= 0 and h <= 0:
            return True

        # Handle centered sprites
        if getattr(node, "centered", False):
            gx -= w / 2
            gy -= h / 2

        return viewport.colliderect(pygame.Rect(int(gx), int(gy), w, h))

    # ==================================================================
    # Debug: bounding boxes, collision shapes, node names
    # ==================================================================

    def _overlay_debug(
        self,
        nodes: List[Node2D],
        surface: pygame.Surface,
    ) -> None:
        font = self._get_small_font()

        for node in nodes:
            sx, sy = node.get_screen_position()

            # ── bounding box / circle ──
            w = getattr(node, "width", 0) or 0
            h = getattr(node, "height", 0) or 0
            if w == 0:
                w = getattr(node, "frame_width", 0) or 0
            if h == 0:
                h = getattr(node, "frame_height", 0) or 0

            scale_x = getattr(node, "scale_x", 1.0)
            scale_y = getattr(node, "scale_y", 1.0)
            radius = getattr(node, "radius", 0) or 0

            if radius and w == 0 and h == 0:
                pygame.draw.circle(
                    surface, _CLR_BBOX,
                    (int(sx), int(sy)),
                    int(radius * max(scale_x, scale_y)),
                    1,
                )
            elif w > 0 and h > 0:
                sw, sh = int(w * scale_x), int(h * scale_y)
                dx, dy = int(sx), int(sy)
                if getattr(node, "centered", False):
                    dx -= sw // 2
                    dy -= sh // 2
                pygame.draw.rect(surface, _CLR_BBOX, (dx, dy, sw, sh), 1)

            # ── collision shape ──
            if Collider2D is not None and isinstance(node, Collider2D):
                cw = int(node.width * node.scale_x)
                ch = int(node.height * node.scale_y)
                if cw > 0 and ch > 0:
                    overlay = pygame.Surface((cw, ch), pygame.SRCALPHA)
                    overlay.fill((*_CLR_COLLIDER, 40))
                    surface.blit(overlay, (int(sx), int(sy)))
                    pygame.draw.rect(
                        surface, _CLR_COLLIDER,
                        (int(sx), int(sy), cw, ch), 1,
                    )

            # ── node name ──
            label = font.render(node.name, True, _CLR_NAME)
            surface.blit(label, (int(sx), int(sy) - 12))

    # ==================================================================
    # Debug: FPS + node-count HUD
    # ==================================================================

    def _overlay_hud(
        self,
        surface: pygame.Surface,
        screen_w: int,
        screen_h: int,
        engine: Optional["Engine"] = None,
    ) -> None:
        font = self._get_font()
        fps = engine.fps if engine else self._fps

        lines = [
            f"FPS: {fps:.1f}",
            f"Rendered: {self._rendered_count}",
            f"Total nodes: {self._total_count}",
        ]

        pad = 6
        line_h = 16
        box_w = 180
        box_h = len(lines) * line_h + pad * 2

        bg = pygame.Surface((box_w, box_h), pygame.SRCALPHA)
        bg.fill(_CLR_HUD_BG)
        surface.blit(bg, (screen_w - box_w - 4, 4))

        for i, text in enumerate(lines):
            lbl = font.render(text, True, _CLR_HUD_TEXT)
            surface.blit(lbl, (screen_w - box_w + pad - 2, 4 + pad + i * line_h))

    # ==================================================================
    # Internal helpers
    # ==================================================================

    def _tick_fps(self) -> None:
        self._frame_count += 1
        now = time.perf_counter()
        elapsed = now - self._last_fps_time
        if elapsed >= 1.0:
            self._fps = self._frame_count / elapsed
            self._frame_count = 0
            self._last_fps_time = now

    def _get_font(self) -> pygame.font.Font:
        if self._font is None:
            pygame.font.init()
            self._font = pygame.font.SysFont("Arial", 14, bold=True)
        return self._font

    def _get_small_font(self) -> pygame.font.Font:
        if self._small_font is None:
            pygame.font.init()
            self._small_font = pygame.font.SysFont("Arial", 11)
        return self._small_font


# ═══════════════════════════════════════════════════════════════════════════
#  Module-level helpers
# ═══════════════════════════════════════════════════════════════════════════

def _z_sort_key(node: Node2D):
    """Sort key: nodes with lower z_index are drawn first (behind)."""
    return getattr(node, "z_index", 0)


def _always_include(node: Node2D) -> bool:
    """Return True for node types that handle their own internal culling."""
    if TilemapNode is not None and isinstance(node, TilemapNode):
        return True
    if ParticleEmitter2D is not None and isinstance(node, ParticleEmitter2D):
        return True
    return False
