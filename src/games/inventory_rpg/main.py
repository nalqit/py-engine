import pygame
import sys
import math
import random

from src.engine.scene.node2d import Node2D
from src.engine.scene.rectangle_node import RectangleNode
from src.engine.scene.circle_node import CircleNode
from src.engine.collision.collider2d import Collider2D
from src.engine.collision.collision_world import CollisionWorld
from src.engine.physics.physics_body_2d import PhysicsBody2D
from src.engine.fsm.state_machine import StateMachine
from src.engine.fsm.state import State
from src.engine.utils.profiler import EngineProfiler
from src.engine.ui.font_cache import FontCache

VIRTUAL_W, VIRTUAL_H = 800, 600

# Procedural Item Generation
TEMPLATES = [
    ("Iron Sword", "Weapon", 10, 0),
    ("Steel Axe", "Weapon", 15, -2),
    ("Dagger of Speed", "Weapon", 5, 5),
    ("Leather Armor", "Armor", 0, 0, 5), # hp +5
    ("Chainmail", "Armor", 0, -5, 15),
    ("Ring of Health", "Accessory", 0, 0, 20),
    ("Boots of Haste", "Accessory", 0, 10, 0)
]
RARITIES = ["Common", "Uncommon", "Rare", "Epic", "Legendary"]

class Item:
    def __init__(self, id_val):
        self.id = id_val
        t = random.choice(TEMPLATES)
        self.name = t[0]
        self.type = t[1]
        
        self.rarity = random.choice(RARITIES)
        r_mult = RARITIES.index(self.rarity) + 1
        
        self.atk = t[2] * r_mult + random.randint(0, r_mult)
        self.spd = t[3] * r_mult
        self.hp = (t[4] if len(t) > 4 else 0) * r_mult + random.randint(0, r_mult * 5)
        self.value = 10 * r_mult * r_mult
        
    def get_display_name(self):
        return f"{self.rarity} {self.name}"

class RPGPlayer(PhysicsBody2D):
    def __init__(self, name, x, y, cw):
        col = Collider2D(name+"Col", 0, 0, 20, 20)
        col.layer = "player"
        col.mask = {"wall"}
        super().__init__(name, x, y, col, cw)
        self.use_gravity = False
        self.base_speed = 200.0
        self.base_hp = 100
        self.base_atk = 10
        
        self.add_child(col)
        self.add_child(RectangleNode("PVis", 0, 0, 20, 20, (50, 150, 255)))
        
        # RPG Data
        self.inventory = [Item(i) for i in range(500)] # 500+ items mass data scaling test
        self.equipped = {"Weapon": None, "Armor": None, "Accessory": None}
        
    def get_max_hp(self):
        hp = self.base_hp
        for v in self.equipped.values():
            if v: hp += v.hp
        return hp
        
    def get_atk(self):
        atk = self.base_atk
        for v in self.equipped.values():
            if v: atk += v.atk
        return atk
        
    def get_speed(self):
        spd = self.base_speed
        for v in self.equipped.values():
            if v: spd += v.spd
        return max(50.0, spd)

# UI State Machine
class OverworldState(State):
    def update(self, delta):
        # Allow movement
        keys = pygame.key.get_pressed()
        p = self.body.player
        mx, my = 0, 0
        if keys[pygame.K_LEFT]: mx -= 1
        if keys[pygame.K_RIGHT]: mx += 1
        if keys[pygame.K_UP]: my -= 1
        if keys[pygame.K_DOWN]: my += 1
        
        if mx != 0 and my != 0:
            length = math.hypot(mx, my)
            mx /= length; my /= length
            
        p.velocity_x = mx * p.get_speed()
        p.velocity_y = my * p.get_speed()
        
        # Toggle inventory (using edge detection)
        if keys[pygame.K_i] and not self.body.keys_last_frame.get(pygame.K_i, False):
            self.body.fsm.change_state(InventoryState(self.body))

class InventoryState(State):
    def enter(self):
        self.body.player.velocity_x = 0
        self.body.player.velocity_y = 0
        self.body.cursor_idx = 0
        
    def update(self, delta):
        keys = pygame.key.get_pressed()
        last = self.body.keys_last_frame
        
        if keys[pygame.K_i] and not last.get(pygame.K_i, False):
            self.body.fsm.change_state(OverworldState(self.body))
            return
            
        if keys[pygame.K_DOWN] and not last.get(pygame.K_DOWN, False):
            self.body.cursor_idx = min(len(self.body.player.inventory) - 1, self.body.cursor_idx + 1)
        if keys[pygame.K_UP] and not last.get(pygame.K_UP, False):
            self.body.cursor_idx = max(0, self.body.cursor_idx - 1)
            
        if keys[pygame.K_RETURN] and not last.get(pygame.K_RETURN, False):
            if len(self.body.player.inventory) > 0:
                self.body.selected_item = self.body.player.inventory[self.body.cursor_idx]
                self.body.fsm.change_state(ItemDetailState(self.body))

class ItemDetailState(State):
    def update(self, delta):
        keys = pygame.key.get_pressed()
        last = self.body.keys_last_frame
        
        if keys[pygame.K_ESCAPE] and not last.get(pygame.K_ESCAPE, False):
            self.body.fsm.change_state(InventoryState(self.body))
            
        if keys[pygame.K_e] and not last.get(pygame.K_e, False):
            # Equip
            item = self.body.selected_item
            if item.type in self.body.player.equipped:
                self.body.player.equipped[item.type] = item
            self.body.fsm.change_state(InventoryState(self.body))

class UIManager(Node2D):
    def __init__(self, name, player):
        super().__init__(name, 0, 0)
        self.player = player
        self.font = pygame.font.SysFont("Arial", 18)
        self.title_font = pygame.font.SysFont("Arial", 24, bold=True)
        
        self.fsm = StateMachine(self)
        self.keys_last_frame = {}
        self.cursor_idx = 0
        self.selected_item = None
        
        self.fsm.change_state(OverworldState(self))
        
    def update(self, delta):
        self.fsm.update(delta)
        k = pygame.key.get_pressed()
        # dict snapshot for edge triggers
        self.keys_last_frame = {key: k[key] for key in [pygame.K_i, pygame.K_UP, pygame.K_DOWN, pygame.K_RETURN, pygame.K_ESCAPE, pygame.K_e]}
        super().update(delta)
        
    def render(self, surface):
        state = self.fsm.current_state
        if isinstance(state, OverworldState):
            # Just overworld HUD
            self.draw_text_cached(surface, "Press 'I' to open Inventory (500 items)", 10, 10, (255, 255, 255))
            self.draw_text_cached(surface, f"HP: {self.player.get_max_hp()} | ATK: {self.player.get_atk()} | SPD: {self.player.get_speed():.0f}", 10, 30, (200, 255, 200))
        else:
            # Inventory UI Root
            pygame.draw.rect(surface, (30, 30, 40, 230), (50, 50, VIRTUAL_W - 100, VIRTUAL_H - 100))
            pygame.draw.rect(surface, (200, 200, 200), (50, 50, VIRTUAL_W - 100, VIRTUAL_H - 100), 2)
            
            self.draw_text_cached(surface, f"INVENTORY ({len(self.player.inventory)} ITEMS)", 70, 70, (255, 255, 255), True)
            
            # --- SCROLL VIRTUALIZATION ---
            # Instead of rendering 500 lines and clipping, we only iterate the visible window
            item_h = 25
            visible_count = 15
            start_row = max(0, self.cursor_idx - visible_count // 2)
            end_row = min(len(self.player.inventory), start_row + visible_count)
            
            # Adjust if we hit the bottom
            if end_row - start_row < visible_count and len(self.player.inventory) > visible_count:
                end_row = len(self.player.inventory)
                start_row = end_row - visible_count
            
            y_offset = 110
            for i in range(start_row, end_row):
                item = self.player.inventory[i]
                color = (255, 255, 100) if i == self.cursor_idx else (200, 200, 200)
                
                # Check if equipped
                eq = ""
                if self.player.equipped.get(item.type) == item:
                    eq = " [E]"
                    color = (100, 255, 100)
                    
                text = f"{item.get_display_name()}{eq}"
                self.draw_text_cached(surface, text, 80, y_offset, color)
                
                # Stats inline
                stats = f"ATK:{item.atk} SPD:{item.spd} HP:{item.hp}"
                self.draw_text_cached(surface, stats, 400, y_offset, (150, 150, 150))
                
                y_offset += item_h
                
            # Scrollbar 
            if len(self.player.inventory) > visible_count:
                bar_h = (visible_count / len(self.player.inventory)) * (visible_count * item_h)
                bar_y = 110 + (start_row / len(self.player.inventory)) * (visible_count * item_h)
                pygame.draw.rect(surface, (100, 100, 100), (680, 110, 10, visible_count * item_h))
                pygame.draw.rect(surface, (200, 200, 200), (680, bar_y, 10, bar_h))

            # Nested State Overlay
            if isinstance(state, ItemDetailState) and self.selected_item:
                item = self.selected_item
                pygame.draw.rect(surface, (50, 50, 80), (200, 200, 400, 200))
                pygame.draw.rect(surface, (255, 255, 255), (200, 200, 400, 200), 2)
                
                self.draw_text_cached(surface, item.get_display_name(), 220, 220, (255, 255, 100), True)
                self.draw_text_cached(surface, f"Type: {item.type}", 220, 260, (200, 200, 200))
                self.draw_text_cached(surface, f"Grants: ATK +{item.atk}, SPD +{item.spd}, HP +{item.hp}", 220, 290, (150, 255, 150))
                
                self.draw_text_cached(surface, "[E] to Equip   |   [ESC] to Back", 220, 350, (255, 255, 255))
        super().render(surface)
        
    def draw_text_cached(self, surface, text, x, y, color, title=False):
        font = self.title_font if title else self.font
        # Use Engine FontCache for massive speedup on 500+ string UI
        surf = FontCache.get_text_surface(font, text, color)
        surface.blit(surf, (x, y))

def main():
    global profiler
    pygame.init()
    screen = pygame.display.set_mode((VIRTUAL_W, VIRTUAL_H), pygame.RESIZABLE)
    game_surface = pygame.Surface((VIRTUAL_W, VIRTUAL_H))
    pygame.display.set_caption("Level 10: Inventory RPG (Nested FSM & Data Scaling)")
    clock = pygame.time.Clock()
    
    profiler = EngineProfiler()
    
    root = Node2D("Root")
    cw = CollisionWorld("CollisionWorld")
    root.add_child(cw)
    
    # Simple Overworld Box
    w1 = Node2D("W1", 100, 100)
    w1c = Collider2D("W1c", 0, 0, 600, 20, is_static=True)
    w1c.mask = {"player"}; w1c.layer = "wall"
    w1.add_child(w1c)
    w1.add_child(RectangleNode("W1v", 0, 0, 600, 20, (100, 50, 50)))
    root.add_child(w1)
    
    w2 = Node2D("W2", 100, 400)
    w2c = Collider2D("W2c", 0, 0, 600, 20, is_static=True)
    w2c.mask = {"player"}; w2c.layer = "wall"
    w2.add_child(w2c)
    w2.add_child(RectangleNode("W2v", 0, 0, 600, 20, (100, 50, 50)))
    root.add_child(w2)
    
    player = RPGPlayer("Player", 300, 250, cw)
    root.add_child(player)
    
    # UI Manager lives at the very end of the tree to render on top
    ui = UIManager("UI", player)
    root.add_child(ui)
    
    font = pygame.font.SysFont("Arial", 16)
    
    running = True
    fixed_dt = 1/60.0
    accumulator = 0.0
    
    while running:
        dt = clock.tick(60) / 1000.0
        profiler.log_frame(dt)
        accumulator += dt
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                
        profiler.begin("Logic")
        while accumulator >= fixed_dt:
            root.update_transforms()
            root.update(fixed_dt)
            accumulator -= fixed_dt
        profiler.end("Logic")
            
        profiler.begin("Render")
        game_surface.fill((20, 60, 30))
        root.render(game_surface)
        
        hits, misses = FontCache.get_stats()
        hud_lines = [
            f"FPS: {clock.get_fps():.1f}",
            f"Font Cache: {hits} hits, {misses} misses",
            f"Mem: {profiler.get_memory_mb():.1f} MB"
        ]
        
        y = VIRTUAL_H - 70
        for line in hud_lines:
            txt = font.render(line, True, (255, 255, 255))
            game_surface.blit(txt, (10, y))
            y += 20
        profiler.end("Render")
            
        scaled = pygame.transform.scale(game_surface, screen.get_size())
        screen.blit(scaled, (0, 0))
        pygame.display.flip()
        
    profiler.print_summary()
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
