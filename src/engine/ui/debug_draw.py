import pygame

class DebugDraw:
    enabled = True

    @staticmethod
    def draw_collider(screen, collider, camera):
        if not DebugDraw.enabled:
            return

        rect = collider.get_rect().copy()
        rect.x -= camera.x
        rect.y -= camera.y

        if collider.is_trigger:
            color = (255, 0, 0)
        elif collider.is_static:
            color = (0, 255, 0)
        else:
            color = (0, 0, 255)

        pygame.draw.rect(screen, color, rect, 2)
