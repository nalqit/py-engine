from src.engine.scene.node2d import Node2D
from src.engine.collision.collider2d import Collider2D



class CollisionWorld(Node2D):
    def __init__(self, name):
        super().__init__(name)
        self._last_collisions = set()

    def _walk(self, node):
        """هذه الدالة تستخدم للتكرار عبر جميع العقد في الشجرة"""
        for child in node.children:
            yield child
            yield from self._walk(child)

    def check_collision(self, collider, test_x, test_y, margin=(0, 0)):
        # rect الحالي
        rect = collider.get_rect()

        dx = test_x - collider.parent.local_x
        dy = test_y - collider.parent.local_y

        # Move then inflate (shrink if negative)
        test_rect = rect.move(dx, dy).inflate(margin[0], margin[1])

        # نطلع للجذر
        root = self
        while root.parent:
            root = root.parent

        # نمشي على كل الشجرة
        for node in self._walk(root):
            if not isinstance(node, Collider2D):
                continue

            other = node

            if other is collider:
                continue

            if other.layer not in collider.mask:
                continue

            # Triggers do not block movement
            if other.is_trigger:
                continue

            if test_rect.colliderect(other.get_rect()):
                return other

        return None

    def process_collisions(self):
        """Call this once per frame"""
        # نطلع للجذر
        root = self
        while root.parent:
            root = root.parent

        # نجمع كل الـ Colliders في المشهد
        all_colliders = []
        for node in self._walk(root):
            if isinstance(node, Collider2D):
                all_colliders.append(node)

        current = set()

        for i, a in enumerate(all_colliders):
            for b in all_colliders[i + 1 :]:
                # الفلترة الأساسية (Symmetric check)
                # Check if A masks B OR B masks A
                a_sees_b = b.layer in a.mask
                b_sees_a = a.layer in b.mask

                if not a_sees_b and not b_sees_a:
                    continue

                if a.get_rect().colliderect(b.get_rect()):
                    pair = tuple(sorted((a, b), key=id))
                    current.add(pair)

                    if pair not in self._last_collisions:
                        self._emit(a, b, "enter")
                    else:
                        self._emit(a, b, "stay")

        # exited
        for pair in self._last_collisions - current:
            a, b = pair
            self._emit(a, b, "exit")

        self._last_collisions = current

    def _emit(self, a, b, phase):
        for col, other in ((a, b), (b, a)):
            body = col.parent
            if not body:
                continue

            method = f"on_collision_{phase}"
            if hasattr(body, method):
                getattr(body, method)(other)
