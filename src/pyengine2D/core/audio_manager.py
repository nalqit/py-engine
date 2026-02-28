import pygame
import os

class AudioManager:
    """
    Handles sound and music playback globally.
    Powered by pygame.mixer.
    """
    
    def __init__(self):
        # Cache for loaded Sound objects
        self.sounds = {}
        # Global volume controls (0.0 to 1.0)
        self.sfx_volume = 1.0
        self.music_volume = 1.0
        
        # Verify mixer initializes cleanly
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init()
            self.is_initialized = True
        except pygame.error as e:
            print(f"AudioManager init failed: {e}")
            self.is_initialized = False

    def load_sound(self, name, path):
        """Pre-load a sound file into memory."""
        if not self.is_initialized: return
        
        if not os.path.exists(path):
            print(f"AudioManager: Sound file not found: {path}")
            return
            
        try:
            sound = pygame.mixer.Sound(path)
            sound.set_volume(self.sfx_volume)
            self.sounds[name] = sound
        except pygame.error as e:
            print(f"AudioManager: Failed loading {path}: {e}")

    def play_sound(self, name, volume=None):
        """Play a pre-loaded sound by name."""
        if not self.is_initialized or name not in self.sounds:
            return
            
        sound = self.sounds[name]
        
        # Override specific clip volume if passed, else use global sfx volume
        vol = volume if volume is not None else self.sfx_volume
        sound.set_volume(vol)
        
        sound.play()

    def play_music(self, path, loops=-1, volume=None):
        """Stream a music file (only one track plays at a time)."""
        if not self.is_initialized: return
        
        if not os.path.exists(path):
            print(f"AudioManager: Music file not found: {path}")
            return
            
        try:
            pygame.mixer.music.load(path)
            vol = volume if volume is not None else self.music_volume
            pygame.mixer.music.set_volume(vol)
            pygame.mixer.music.play(loops=loops)
        except pygame.error as e:
            print(f"AudioManager: Failed playing music {path}: {e}")

    def stop_music(self):
        if self.is_initialized:
            pygame.mixer.music.stop()

    def set_sfx_volume(self, volume):
        """Set volume of all cached and future sound effects (0.0 to 1.0)."""
        self.sfx_volume = max(0.0, min(1.0, volume))
        for sound in self.sounds.values():
            sound.set_volume(self.sfx_volume)

    def set_music_volume(self, volume):
        """Set volume of streaming music (0.0 to 1.0)."""
        if self.is_initialized:
            self.music_volume = max(0.0, min(1.0, volume))
            pygame.mixer.music.set_volume(self.music_volume)
