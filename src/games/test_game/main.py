"""
test_game — minimal project to validate the PyEngine 2D IDE.

Loads a scene from JSON and starts the engine loop.
"""

import sys
import os

# Ensure the engine package is importable.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from pyengine2D.core.engine import Engine  # noqa: E402
from pyengine2D.scene.scene_serializer import SceneSerializer
from pyengine2D.scene.scene_manager import Scene
import os


def main() -> None:
    engine = Engine(
        title="PyEngine 2D — Test Game",
        virtual_w=800,
        virtual_h=600,
    )

    # Use absolute path relative to this script so it runs from anywhere
    base_dir = os.path.dirname(os.path.abspath(__file__))
    scene_path = os.path.join(base_dir, "scenes", "level_1.scene")
    
    # Load the scene tree from the JSON definition using the serializer
    root_node = SceneSerializer.load(scene_path)
    
    # Wrap in a Scene so the SceneManager can handle it
    main_scene = Scene("MainScene")
    main_scene.add_child(root_node)
    
    engine.scene_manager.switch_scene(main_scene)

    # Start the engine loop (input → update → render).
    engine.run()


if __name__ == "__main__":
    main()
