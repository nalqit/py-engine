import random

from src.engine.core.engine import Engine
from src.engine.core.input import Keys
from src.engine.scene.node2d import Node2D
from src.engine.scene.rectangle_node import RectangleNode
from src.engine.scene.circle_node import CircleNode
from src.engine.time.master_clock import MasterClock
from src.engine.utils.profiler import EngineProfiler

VIRTUAL_W, VIRTUAL_H = 800, 600
COLS = [250, 350, 450, 550]
JUDGEMENT_Y = 500
NOTE_SPEED = 600.0
COL_KEYS = [Keys.D, Keys.F, Keys.J, Keys.K]


class Note(Node2D):
    def __init__(self, name, col_idx, target_time):
        super().__init__(name, COLS[col_idx], -100)
        self.col_idx = col_idx
        self.target_time = target_time
        colors = [(255, 100, 100), (100, 255, 100), (100, 100, 255), (255, 255, 100)]
        self.add_child(RectangleNode(name + "Vis", -20, -10, 40, 20, colors[col_idx]))
        self.hit = False

    def update_position(self, current_time):
        time_diff = self.target_time - current_time
        self.local_y = JUDGEMENT_Y - (time_diff * NOTE_SPEED)


class HitEffect(Node2D):
    def __init__(self, name, x, y, text):
        super().__init__(name, x, y)
        self.timer = 0.5
        self.text = text
        self.vis = CircleNode(name + "C", 0, 0, 10, (255, 255, 255))
        self.add_child(self.vis)

    def update(self, delta):
        self.timer -= delta
        self.local_y -= 50 * delta
        self.vis.radius += 50 * delta
        if self.timer <= 0 and self.parent:
            self.parent.remove_child(self)
        super().update(delta)


class RhythmGameNode(Node2D):
    def __init__(self, name, clock):
        super().__init__(name, 0, 0)
        self.master_clock = clock
        self.notes = []
        self.next_beat_time = 1.0
        self.beat_interval = 0.4
        self.score = 0
        self.combo = 0
        self.max_combo = 0
        self.add_child(RectangleNode("JLine", 150, JUDGEMENT_Y - 2, 500, 4, (200, 200, 200)))
        self.key_states = [False] * 4

    def update(self, delta):
        inp = Engine.instance.input
        current_time = self.master_clock.get_time()
        lookahead = 2.0
        while self.next_beat_time < current_time + lookahead:
            col = random.randint(0, 3)
            self.notes.append(n := Note(f"Note_{self.next_beat_time}", col, self.next_beat_time))
            self.add_child(n)
            self.next_beat_time += self.beat_interval
            if random.random() < 0.2:
                col2 = (col + random.randint(1, 3)) % 4
                self.notes.append(n2 := Note(f"Note_{self.next_beat_time}b", col2, self.next_beat_time - self.beat_interval))
                self.add_child(n2)

        missed = [n for n in self.notes if current_time > n.target_time + 0.1]
        for m in missed:
            self.notes.remove(m)
            self.remove_child(m)
            self.combo = 0
            self.add_child(HitEffect(f"Eff_{random.randint(0, 999)}", m.local_x, m.local_y, "Miss"))

        for n in self.notes:
            n.update_position(current_time)

        for i, k in enumerate(COL_KEYS):
            is_pressed = inp.is_key_pressed(k)
            if is_pressed and not self.key_states[i]:
                self.handle_hit(i, current_time)
            self.key_states[i] = is_pressed
        super().update(delta)

    def handle_hit(self, col_idx, current_time):
        target_note = next((n for n in self.notes if n.col_idx == col_idx), None)
        if not target_note:
            return
        diff = abs(target_note.target_time - current_time)
        if diff <= 0.030:
            self.score += 100; self.combo += 1
            self.spawn_effect(target_note.local_x, "Perfect")
        elif diff <= 0.080:
            self.score += 50; self.combo += 1
            self.spawn_effect(target_note.local_x, "Good")
        elif target_note.target_time > current_time and diff < 0.2:
            self.combo = 0
            self.spawn_effect(target_note.local_x, "Early")
        else:
            return
        self.notes.remove(target_note)
        self.remove_child(target_note)
        self.max_combo = max(self.max_combo, self.combo)

    def spawn_effect(self, x, text):
        self.add_child(HitEffect(f"Eff_{random.randint(0, 999)}", x, JUDGEMENT_Y, text))


def main():
    engine = Engine("Level 7: Rhythm Game (Absolute MasterClock Sync)", VIRTUAL_W, VIRTUAL_H)
    profiler = EngineProfiler()
    engine_clock = MasterClock()
    r = engine.renderer
    surface = engine.game_surface

    root = Node2D("Root")
    game = RhythmGameNode("Game", engine_clock)
    root.add_child(game)

    start_sys_ticks = engine.get_ticks_ms()
    last_drift_check = 0.0
    accumulator = 0.0

    while engine.running:
        dt = engine.begin_frame()
        profiler.log_frame(dt)
        accumulator += dt

        profiler.begin("Logic")
        while accumulator >= engine.fixed_dt:
            engine_clock.update(engine.fixed_dt)
            if engine_clock.elapsed - last_drift_check >= 10.0:
                last_drift_check = engine_clock.elapsed
                sys_elapsed = (engine.get_ticks_ms() - start_sys_ticks) / 1000.0
                drift_ms = abs(sys_elapsed - engine_clock.elapsed) * 1000.0
                print(f"[DRIFT MONITOR] Engine {engine_clock.elapsed:.3f}s vs Sys {sys_elapsed:.3f}s | Diff: {drift_ms:.2f}ms")
                if drift_ms > 5.0:
                    print(f"WARNING: Drift exceeded 5ms! ({drift_ms:.2f}ms)")
            root.update_transforms()
            root.update(engine.fixed_dt)
            accumulator -= engine.fixed_dt
        profiler.end("Logic")

        profiler.begin("Render")
        r.fill(surface, (10, 10, 30))
        for i, cx in enumerate(COLS):
            col_color = (255, 255, 255) if game.key_states[i] else (150, 150, 150)
            r.draw_rect(surface, col_color, cx - 30, JUDGEMENT_Y - 10, 60, 20, 2)
            lbl = r.render_text(["D", "F", "J", "K"][i], (100, 100, 100))
            r.blit(surface, lbl, (cx - lbl.get_width() // 2, JUDGEMENT_Y + 20))
        root.render(surface)
        for c in game.children:
            if isinstance(c, HitEffect):
                txt = r.render_text_uncached(c.text, (255, 255, 255), size=60, bold=True)
                r.blit(surface, txt, (c.local_x - txt.get_width() // 2, c.local_y - 30))
        hud = [
            f"FPS: {engine.fps:.1f}", f"Score: {game.score}", f"Combo: {game.combo}",
            f"Max Combo: {game.max_combo}", f"Engine Time: {engine_clock.elapsed:.2f}s"
        ]
        y = 10
        for line in hud:
            r.blit(surface, r.render_text_uncached(line, (255, 255, 255)), (10, y))
            y += 20
        profiler.end("Render")
        engine.end_frame()

    profiler.print_summary()
    engine.quit()


if __name__ == "__main__":
    main()
