import pygame


class Keys:
    """Engine key constants. Abstracts pygame key codes."""
    LEFT = pygame.K_LEFT
    RIGHT = pygame.K_RIGHT
    UP = pygame.K_UP
    DOWN = pygame.K_DOWN
    SPACE = pygame.K_SPACE
    RETURN = pygame.K_RETURN
    ESCAPE = pygame.K_ESCAPE
    LSHIFT = pygame.K_LSHIFT

    A = pygame.K_a
    B = pygame.K_b
    D = pygame.K_d
    E = pygame.K_e
    F = pygame.K_f
    I = pygame.K_i
    J = pygame.K_j
    K = pygame.K_k
    L = pygame.K_l
    R = pygame.K_r
    S = pygame.K_s
    W = pygame.K_w

    NUM_1 = pygame.K_1
    NUM_2 = pygame.K_2
    NUM_3 = pygame.K_3
    NUM_4 = pygame.K_4


class InputSystem:
    """Engine input abstraction. Wraps all keyboard and mouse state."""

    def __init__(self, engine):
        self._engine = engine
        self._keys = {}
        self._prev_keys = {}
        self._mouse_buttons = (False, False, False)
        self._mouse_pos = (0, 0)

    def _update(self):
        self._prev_keys = dict(self._keys)
        pressed = pygame.key.get_pressed()
        self._keys = {i: bool(pressed[i]) for i in range(len(pressed))}
        self._mouse_buttons = pygame.mouse.get_pressed()
        mx, my = pygame.mouse.get_pos()
        sw, sh = pygame.display.get_surface().get_size()
        vw, vh = self._engine.virtual_w, self._engine.virtual_h
        self._mouse_pos = (mx * (vw / max(1, sw)), my * (vh / max(1, sh)))

    def is_key_pressed(self, key):
        return self._keys.get(key, False)

    def is_key_just_pressed(self, key):
        return self._keys.get(key, False) and not self._prev_keys.get(key, False)

    def get_mouse_pos(self):
        """Returns mouse position in virtual (world) coordinates."""
        return self._mouse_pos

    def is_mouse_pressed(self, button=0):
        return self._mouse_buttons[button]
