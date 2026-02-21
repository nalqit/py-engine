import pygame
import sys
import random

from src.engine.scene.node2d import Node2D
from src.engine.scene.rectangle_node import RectangleNode
from src.engine.scene.circle_node import CircleNode
from src.engine.time.master_clock import MasterClock
from src.engine.utils.profiler import EngineProfiler

VIRTUAL_W, VIRTUAL_H = 800, 600

# 4 Columns: D, F, J, K
COLS = [250, 350, 450, 550]
JUDGEMENT_Y = 500
NOTE_SPEED = 600.0  # pixels per second

class Note(Node2D):
    def __init__(self, name, col_idx, target_time):
        super().__init__(name, COLS[col_idx], -100)
        self.col_idx = col_idx
        self.target_time = target_time
        
        # Color based on column
        colors = [(255, 100, 100), (100, 255, 100), (100, 100, 255), (255, 255, 100)]
        self.add_child(RectangleNode(name+"Vis", -20, -10, 40, 20, colors[col_idx]))
        self.hit = False
        
    def update_position(self, current_time):
        # Time-based absolute positioning (solves physics integration drift)
        time_diff = self.target_time - current_time
        self.local_y = JUDGEMENT_Y - (time_diff * NOTE_SPEED)

class HitEffect(Node2D):
    def __init__(self, name, x, y, text):
        super().__init__(name, x, y)
        self.timer = 0.5
        self.text = text
        self.vis = CircleNode(name+"C", 0, 0, 10, (255, 255, 255))
        self.add_child(self.vis)
        
    def update(self, delta):
        self.timer -= delta
        self.local_y -= 50 * delta
        self.vis.radius += 50 * delta
        if self.timer <= 0:
            if self.parent:
                self.parent.remove_child(self)
        super().update(delta)

class RhythmGameNode(Node2D):
    def __init__(self, name, clock):
        super().__init__(name, 0, 0)
        self.master_clock = clock
        self.notes = []
        
        self.next_beat_time = 1.0
        self.beat_interval = 0.4 # 150 BPM
        
        self.score = 0
        self.combo = 0
        self.max_combo = 0
        
        # Draw Judgment Line
        self.add_child(RectangleNode("JLine", 150, JUDGEMENT_Y-2, 500, 4, (200, 200, 200)))
        
        self.keys = [pygame.K_d, pygame.K_f, pygame.K_j, pygame.K_k]
        self.key_states = [False] * 4
        
    def update(self, delta):
        current_time = self.master_clock.get_time()
        
        # Procedural note generation for marathon test
        # Spawning notes 2 seconds ahead of their target time
        lookahead = 2.0
        while self.next_beat_time < current_time + lookahead:
            col = random.randint(0, 3)
            n = Note(f"Note_{self.next_beat_time}", col, self.next_beat_time)
            self.notes.append(n)
            self.add_child(n)
            self.next_beat_time += self.beat_interval
            
            # Double note chance
            if random.random() < 0.2:
                col2 = (col + random.randint(1, 3)) % 4
                n2 = Note(f"Note_{self.next_beat_time}b", col2, self.next_beat_time - self.beat_interval)
                self.notes.append(n2)
                self.add_child(n2)
        
        # Update note properties
        missed = []
        for n in self.notes:
            n.update_position(current_time)
            # Miss detection (100ms past target)
            if current_time > n.target_time + 0.1:
                missed.append(n)
                
        for m in missed:
            self.notes.remove(m)
            self.remove_child(m)
            self.combo = 0
            self.spawn_effect(m.local_x, m.local_y, "Miss")
            
        # Input handling
        pressed = pygame.key.get_pressed()
        for i, k in enumerate(self.keys):
            is_pressed = pressed[k]
            if is_pressed and not self.key_states[i]:
                # Just pressed
                self.handle_hit(i, current_time)
            self.key_states[i] = is_pressed
            
        super().update(delta)
        
    def handle_hit(self, col_idx, current_time):
        # Audio simulation: fire and forget beep (can use pygame.mixer here but clock is internal)
        # Not including actual audio files to keep code runnable standalone
        
        # Find earliest note in this column
        target_note = None
        for n in self.notes:
            if n.col_idx == col_idx:
                target_note = n
                break
                
        if target_note:
            diff = abs(target_note.target_time - current_time)
            if diff <= 0.030: # 30ms perfect
                self.score += 100
                self.combo += 1
                self.spawn_effect(target_note.local_x, JUDGEMENT_Y, "Perfect")
                self.notes.remove(target_note)
                self.remove_child(target_note)
            elif diff <= 0.080: # 80ms good
                self.score += 50
                self.combo += 1
                self.spawn_effect(target_note.local_x, JUDGEMENT_Y, "Good")
                self.notes.remove(target_note)
                self.remove_child(target_note)
            else:
                # Early press miss
                if target_note.target_time > current_time and diff < 0.2:
                    self.combo = 0
                    self.spawn_effect(target_note.local_x, JUDGEMENT_Y, "Early")
                    self.notes.remove(target_note)
                    self.remove_child(target_note)
            
            self.max_combo = max(self.max_combo, self.combo)

    def spawn_effect(self, x, y, text):
        eff = HitEffect(f"Eff_{random.randint(0,999)}", x, y, text)
        self.add_child(eff)

def main():
    pygame.init()
    screen = pygame.display.set_mode((VIRTUAL_W, VIRTUAL_H), pygame.RESIZABLE)
    game_surface = pygame.Surface((VIRTUAL_W, VIRTUAL_H))
    pygame.display.set_caption("Level 7: Rhythm Game (Absolute MasterClock Sync)")
    sys_clock = pygame.time.Clock()
    
    profiler = EngineProfiler()
    engine_clock = MasterClock()
    
    root = Node2D("Root")
    game = RhythmGameNode("Game", engine_clock)
    root.add_child(game)
    
    font = pygame.font.SysFont("Arial", 20)
    bg_font = pygame.font.SysFont("Arial", 60, bold=True)
    
    # Drift monitor setup
    start_sys_ticks = pygame.time.get_ticks()
    last_drift_check = 0.0
    
    running = True
    fixed_dt = 1/60.0
    accumulator = 0.0
    
    while running:
        dt = sys_clock.tick(60) / 1000.0
        profiler.log_frame(dt)
        accumulator += dt
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                
        profiler.begin("Logic")
        while accumulator >= fixed_dt:
            # The core architectural rule: engine clock advances ONLY by fixed_dt
            engine_clock.update(fixed_dt)
            
            # 10s Drift Check
            if engine_clock.elapsed - last_drift_check >= 10.0:
                last_drift_check = engine_clock.elapsed
                sys_elapsed = (pygame.time.get_ticks() - start_sys_ticks) / 1000.0
                drift_ms = abs(sys_elapsed - engine_clock.elapsed) * 1000.0
                print(f"[DRIFT MONITOR] 10s check: Engine {engine_clock.elapsed:.3f}s vs Sys {sys_elapsed:.3f}s | Diff: {drift_ms:.2f}ms")
                if drift_ms > 5.0:
                    print(f"WARNING: Drift exceeded 5ms! ({drift_ms:.2f}ms)")
            
            root.update_transforms()
            root.update(fixed_dt)
            accumulator -= fixed_dt
        profiler.end("Logic")
            
        profiler.begin("Render")
        game_surface.fill((10, 10, 30))
        
        # Drawing keys hitboxes
        for i, cx in enumerate(COLS):
            col_color = (150, 150, 150) if not game.key_states[i] else (255, 255, 255)
            pygame.draw.rect(game_surface, col_color, (cx-30, JUDGEMENT_Y-10, 60, 20), 2)
            
            # Key labels
            lbl = font.render(["D", "F", "J", "K"][i], True, (100, 100, 100))
            game_surface.blit(lbl, (cx-lbl.get_width()//2, JUDGEMENT_Y+20))
        
        root.render(game_surface)
        
        # Draw hit effects text over everything
        for c in game.children:
            if isinstance(c, HitEffect):
                txt = bg_font.render(c.text, True, (255, 255, 255))
                game_surface.blit(txt, (c.local_x - txt.get_width()//2, c.local_y - 30))
        
        hud_lines = [
            f"FPS: {sys_clock.get_fps():.1f}",
            f"Score: {game.score}",
            f"Combo: {game.combo}",
            f"Max Combo: {game.max_combo}",
            f"Engine Time: {engine_clock.elapsed:.2f}s"
        ]
        
        y = 10
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
