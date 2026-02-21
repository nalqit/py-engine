import math
import random

from src.engine.core.engine import Engine
from src.engine.core.input import Keys
from src.engine.scene.node2d import Node2D
from src.engine.scene.rectangle_node import RectangleNode
from src.engine.collision.collider2d import Collider2D
from src.engine.collision.collision_world import CollisionWorld
from src.engine.physics.physics_body_2d import PhysicsBody2D
from src.engine.fsm.state_machine import StateMachine
from src.engine.fsm.state import State
from src.engine.utils.profiler import EngineProfiler

VIRTUAL_W, VIRTUAL_H = 800, 600

TEMPLATES = [
    ("Iron Sword", "Weapon", 10, 0),
    ("Steel Axe", "Weapon", 15, -2),
    ("Dagger of Speed", "Weapon", 5, 5),
    ("Leather Armor", "Armor", 0, 0, 5),
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
        col = Collider2D(name + "Col", 0, 0, 20, 20)
        col.layer = "player"
        col.mask = {"wall"}
        super().__init__(name, x, y, col, cw)
        self.use_gravity = False
        self.base_speed = 200.0
        self.base_hp = 100
        self.base_atk = 10
        self.add_child(col)
        self.add_child(RectangleNode("PVis", 0, 0, 20, 20, (50, 150, 255)))
        self.inventory = [Item(i) for i in range(500)]
        self.equipped = {"Weapon": None, "Armor": None, "Accessory": None}

    def get_max_hp(self):
        return self.base_hp + sum(v.hp for v in self.equipped.values() if v)

    def get_atk(self):
        return self.base_atk + sum(v.atk for v in self.equipped.values() if v)

    def get_speed(self):
        return max(50.0, self.base_speed + sum(v.spd for v in self.equipped.values() if v))


class OverworldState(State):
    def update(self, delta):
        inp = Engine.instance.input
        p = self.body.player
        mx, my = 0, 0
        if inp.is_key_pressed(Keys.LEFT): mx -= 1
        if inp.is_key_pressed(Keys.RIGHT): mx += 1
        if inp.is_key_pressed(Keys.UP): my -= 1
        if inp.is_key_pressed(Keys.DOWN): my += 1
        if mx != 0 and my != 0:
            length = math.hypot(mx, my)
            mx /= length; my /= length
        p.velocity_x = mx * p.get_speed()
        p.velocity_y = my * p.get_speed()
        if inp.is_key_just_pressed(Keys.I):
            self.body.fsm.change_state(InventoryState(self.body))


class InventoryState(State):
    def enter(self):
        self.body.player.velocity_x = 0
        self.body.player.velocity_y = 0
        self.body.cursor_idx = 0

    def update(self, delta):
        inp = Engine.instance.input
        if inp.is_key_just_pressed(Keys.I):
            self.body.fsm.change_state(OverworldState(self.body)); return
        if inp.is_key_just_pressed(Keys.DOWN):
            self.body.cursor_idx = min(len(self.body.player.inventory) - 1, self.body.cursor_idx + 1)
        if inp.is_key_just_pressed(Keys.UP):
            self.body.cursor_idx = max(0, self.body.cursor_idx - 1)
        if inp.is_key_just_pressed(Keys.RETURN) and self.body.player.inventory:
            self.body.selected_item = self.body.player.inventory[self.body.cursor_idx]
            self.body.fsm.change_state(ItemDetailState(self.body))


class ItemDetailState(State):
    def update(self, delta):
        inp = Engine.instance.input
        if inp.is_key_just_pressed(Keys.ESCAPE):
            self.body.fsm.change_state(InventoryState(self.body))
        if inp.is_key_just_pressed(Keys.E):
            item = self.body.selected_item
            if item.type in self.body.player.equipped:
                self.body.player.equipped[item.type] = item
            self.body.fsm.change_state(InventoryState(self.body))


class UIManager(Node2D):
    def __init__(self, name, player):
        super().__init__(name, 0, 0)
        self.player = player
        self.fsm = StateMachine(self)
        self.cursor_idx = 0
        self.selected_item = None
        self.fsm.change_state(OverworldState(self))

    def update(self, delta):
        self.fsm.update(delta)
        super().update(delta)

    def render(self, surface):
        r = Engine.instance.renderer
        state = self.fsm.current_state
        if isinstance(state, OverworldState):
            r.blit(surface, r.render_text("Press 'I' to open Inventory (500 items)", (255, 255, 255)), (10, 10))
            r.blit(surface, r.render_text_uncached(
                f"HP: {self.player.get_max_hp()} | ATK: {self.player.get_atk()} | SPD: {self.player.get_speed():.0f}",
                (200, 255, 200)), (10, 30))
        else:
            r.draw_rect(surface, (30, 30, 40, 230), 50, 50, VIRTUAL_W - 100, VIRTUAL_H - 100)
            r.draw_rect(surface, (200, 200, 200), 50, 50, VIRTUAL_W - 100, VIRTUAL_H - 100, 2)
            r.blit(surface, r.render_text_uncached(f"INVENTORY ({len(self.player.inventory)} ITEMS)",
                                                    (255, 255, 255), size=24, bold=True), (70, 70))
            item_h = 25
            visible = 15
            start_row = max(0, self.cursor_idx - visible // 2)
            end_row = min(len(self.player.inventory), start_row + visible)
            if end_row - start_row < visible and len(self.player.inventory) > visible:
                end_row = len(self.player.inventory)
                start_row = end_row - visible
            y_off = 110
            for i in range(start_row, end_row):
                item = self.player.inventory[i]
                color = (255, 255, 100) if i == self.cursor_idx else (200, 200, 200)
                eq = ""
                if self.player.equipped.get(item.type) == item:
                    eq = " [E]"; color = (100, 255, 100)
                r.blit(surface, r.render_text_uncached(f"{item.get_display_name()}{eq}", color, size=18), (80, y_off))
                r.blit(surface, r.render_text_uncached(f"ATK:{item.atk} SPD:{item.spd} HP:{item.hp}",
                                                        (150, 150, 150), size=18), (400, y_off))
                y_off += item_h
            if len(self.player.inventory) > visible:
                bar_h = (visible / len(self.player.inventory)) * (visible * item_h)
                bar_y = 110 + (start_row / len(self.player.inventory)) * (visible * item_h)
                r.draw_rect(surface, (100, 100, 100), 680, 110, 10, visible * item_h)
                r.draw_rect(surface, (200, 200, 200), 680, bar_y, 10, bar_h)

            if isinstance(state, ItemDetailState) and self.selected_item:
                item = self.selected_item
                r.draw_rect(surface, (50, 50, 80), 200, 200, 400, 200)
                r.draw_rect(surface, (255, 255, 255), 200, 200, 400, 200, 2)
                r.blit(surface, r.render_text_uncached(item.get_display_name(), (255, 255, 100), size=24, bold=True),
                       (220, 220))
                r.blit(surface, r.render_text_uncached(f"Type: {item.type}", (200, 200, 200), size=18), (220, 260))
                r.blit(surface, r.render_text_uncached(
                    f"Grants: ATK +{item.atk}, SPD +{item.spd}, HP +{item.hp}", (150, 255, 150), size=18), (220, 290))
                r.blit(surface, r.render_text_uncached("[E] to Equip   |   [ESC] to Back",
                                                        (255, 255, 255), size=18), (220, 350))
        super().render(surface)


def main():
    engine = Engine("Level 10: Inventory RPG (Nested FSM & Data Scaling)", VIRTUAL_W, VIRTUAL_H)
    profiler = EngineProfiler()
    r = engine.renderer
    surface = engine.game_surface

    root = Node2D("Root")
    cw = CollisionWorld("CollisionWorld")
    root.add_child(cw)

    w1 = Node2D("W1", 100, 100)
    w1c = Collider2D("W1c", 0, 0, 600, 20, is_static=True)
    w1c.mask = {"player"}; w1c.layer = "wall"
    w1.add_child(w1c); w1.add_child(RectangleNode("W1v", 0, 0, 600, 20, (100, 50, 50)))
    root.add_child(w1)

    w2 = Node2D("W2", 100, 400)
    w2c = Collider2D("W2c", 0, 0, 600, 20, is_static=True)
    w2c.mask = {"player"}; w2c.layer = "wall"
    w2.add_child(w2c); w2.add_child(RectangleNode("W2v", 0, 0, 600, 20, (100, 50, 50)))
    root.add_child(w2)

    player = RPGPlayer("Player", 300, 250, cw)
    root.add_child(player)
    ui = UIManager("UI", player)
    root.add_child(ui)

    accumulator = 0.0
    while engine.running:
        dt = engine.begin_frame()
        profiler.log_frame(dt)
        accumulator += dt

        profiler.begin("Logic")
        while accumulator >= engine.fixed_dt:
            root.update_transforms()
            root.update(engine.fixed_dt)
            accumulator -= engine.fixed_dt
        profiler.end("Logic")

        profiler.begin("Render")
        r.fill(surface, (20, 60, 30))
        root.render(surface)
        hud = [f"FPS: {engine.fps:.1f}", f"Mem: {profiler.get_memory_mb():.1f} MB"]
        y = VIRTUAL_H - 50
        for line in hud:
            r.blit(surface, r.render_text_uncached(line, (255, 255, 255)), (10, y))
            y += 20
        profiler.end("Render")
        engine.end_frame()

    profiler.print_summary()
    engine.quit()


if __name__ == "__main__":
    main()
