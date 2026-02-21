import os
os.environ["SDL_VIDEODRIVER"] = "dummy"

import pygame
import random
import sys

from src.game import main

# State for the fuzzer
frame_count = 0
MAX_FRAMES = 3600  # 60 seconds at 60fps

original_event_get = pygame.event.get
original_key_get_pressed = pygame.key.get_pressed

def fake_event_get(*args, **kwargs):
    global frame_count
    frame_count += 1
    
    events = []
    
    # End the game after MAX_FRAMES
    if frame_count >= MAX_FRAMES:
        quit_event = pygame.event.Event(pygame.QUIT)
        events.append(quit_event)
        
    return events

class FakeKeys:
    def __getitem__(self, key):
        if random.random() < 0.4 and key == pygame.K_RIGHT: return True
        if random.random() < 0.4 and key == pygame.K_LEFT: return True
        if random.random() < 0.05 and key == pygame.K_SPACE: return True
        return False

def fake_key_get_pressed(*args, **kwargs):
    return FakeKeys()

# Patch pygame functions
pygame.event.get = fake_event_get
pygame.key.get_pressed = fake_key_get_pressed

print("Starting Headless Pygame Fuzzer for 3600 frames...")
try:
    main.main()
except SystemExit:
    print("Fuzzer completed cleanly via sys.exit().")
except Exception as e:
    print("CRASH DETECTED!")
    import traceback
    traceback.print_exc()
    sys.exit(1)
