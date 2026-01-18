from src.scene.node import Node
import pygame

class StatsHUD(Node):
    def __init__(self, name="StatsHUD", root_node=None, clock=None):
        super().__init__(name)
        self.root_node = root_node
        self.clock = clock
        self.font = None

    def _count_nodes(self, node):
        count = 1
        for child in node.children:
            count += self._count_nodes(child)
        return count
    
    def _count_colliders(self, node):
        count = 0
        if "Collider" in node.name or "Collider" in str(type(node).__name__):
            count = 1
        for child in node.children:
            count += self._count_colliders(child)
        return count

    def render(self, surface: pygame.Surface) -> None:
        if not self.font:
            self.font = pygame.font.SysFont("Arial", 16)
            
        fps = int(self.clock.get_fps()) if self.clock else 0
        node_count = self._count_nodes(self.root_node) if self.root_node else 0
        collider_count = self._count_colliders(self.root_node) if self.root_node else 0
        
        lines = [
            f"FPS: {fps}",
            f"Nodes: {node_count}",
            f"Colliders: {collider_count}"
        ]
        
        y = 10
        for line in lines:
            text = self.font.render(line, True, (255, 255, 255))
            surface.blit(text, (10, y))
            y += 20
            
        super().render(surface)
