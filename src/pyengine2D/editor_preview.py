import json
import queue
import threading

from src.pyengine2D.core.engine import Engine
from src.pyengine2D.scene.node2d import Node2D
from src.pyengine2D.scene.scene_manager import Scene
from src.pyengine2D.scene.scene_serializer import SceneSerializer


class EditorPreviewHost:
    def __init__(self):
        self.engine = Engine("PyEngine2D Editor Preview", virtual_w=800, virtual_h=600)
        self.command_queue: queue.Queue = queue.Queue()
        self.latest_scene_dict = None
        self.scene_name = "EditorPreviewScene"
        self.node_index = {}
        self._last_fps_int = -1

    def start(self):
        listener = threading.Thread(target=self._stdin_listener, daemon=True)
        listener.start()
        print("Engine started", flush=True)
        self.engine.run(on_fixed_update=self._on_fixed_update)

    def _stdin_listener(self):
        while self.engine.running:
            try:
                line = input()
            except EOFError:
                break
            except Exception:
                continue
            self.command_queue.put(line.strip())

    def _on_fixed_update(self, engine, active_root, fixed_dt):
        self._process_commands()

        fps_int = int(engine.fps)
        if fps_int != self._last_fps_int:
            self._last_fps_int = fps_int
            print(f"FPS: {fps_int}", flush=True)

    def _process_commands(self):
        while True:
            try:
                raw = self.command_queue.get_nowait()
            except queue.Empty:
                return

            if not raw:
                continue

            if raw.startswith("SCENE:"):
                payload = raw[len("SCENE:"):]
                self._handle_scene(payload)
            elif raw.startswith("PATCH:"):
                payload = raw[len("PATCH:"):]
                self._handle_patch(payload)
            elif raw == "PAUSE":
                self.engine.paused = True
                print("ACK:PAUSE", flush=True)
            elif raw == "RESUME":
                self.engine.paused = False
                print("ACK:RESUME", flush=True)
            elif raw == "RESET":
                self._handle_reset()
            elif raw == "QUIT":
                print("ACK:QUIT", flush=True)
                self.engine.running = False
                return
            else:
                print(f"ERROR:unknown_command:{raw}", flush=True)

    def _handle_scene(self, payload):
        try:
            scene_dict = json.loads(payload)
            self.latest_scene_dict = scene_dict
            root = SceneSerializer.from_dict(scene_dict)
            preview_scene = Scene(self.scene_name)
            preview_scene.add_child(root)
            self.engine.scene_manager.switch_scene(preview_scene)
            self.engine.scene_manager.process_pending_changes()
            self._index_active_scene_nodes()
            self._ensure_camera_binding()
            print("ACK:SCENE", flush=True)
        except Exception as exc:
            print(f"ERROR:SCENE:{exc}", flush=True)

    def _handle_reset(self):
        if not self.latest_scene_dict:
            print("ERROR:RESET:no_scene", flush=True)
            return
        try:
            root = SceneSerializer.from_dict(self.latest_scene_dict)
            preview_scene = Scene(self.scene_name)
            preview_scene.add_child(root)
            self.engine.scene_manager.switch_scene(preview_scene)
            self.engine.scene_manager.process_pending_changes()
            self._index_active_scene_nodes()
            self._ensure_camera_binding()
            print("ACK:RESET", flush=True)
        except Exception as exc:
            print(f"ERROR:RESET:{exc}", flush=True)

    def _handle_patch(self, payload):
        try:
            patch = json.loads(payload)
        except Exception as exc:
            print(f"ERROR:PATCH:invalid_json:{exc}", flush=True)
            return

        node_id = patch.get("id")
        if not node_id:
            print("ERROR:PATCH:missing_id", flush=True)
            return

        properties = patch.get("properties")
        if not isinstance(properties, dict):
            print("ERROR:PATCH:missing_properties", flush=True)
            return

        node = self.node_index.get(node_id)
        if node is None:
            self._index_active_scene_nodes()
            node = self.node_index.get(node_id)
        if node is None:
            print(f"ERROR:PATCH:unknown_id:{node_id}", flush=True)
            return

        self._apply_properties(node, properties)
        print(f"ACK:PATCH:{node_id}", flush=True)

    def _apply_properties(self, node, properties):
        for key, value in properties.items():
            if key == "x" and hasattr(node, "local_x"):
                node.local_x = value
            elif key == "y" and hasattr(node, "local_y"):
                node.local_y = value
            elif key == "scale_x" and hasattr(node, "scale_x"):
                node.scale_x = value
            elif key == "scale_y" and hasattr(node, "scale_y"):
                node.scale_y = value
            elif key == "rotation" and hasattr(node, "rotation"):
                node.rotation = value
            elif key == "visible":
                setattr(node, "visible", bool(value))
                if hasattr(node, "set_dirty"):
                    node.set_dirty()
            elif key == "z_index":
                setattr(node, "z_index", int(value))
            elif key == "name":
                node.name = str(value)
            elif hasattr(node, key):
                setattr(node, key, value)

    def _index_active_scene_nodes(self):
        self.node_index = {}
        scene = self.engine.scene_manager.current_scene
        if scene is None:
            return

        def _walk(node):
            node_id = getattr(node, "_editor_id", None)
            if node_id:
                self.node_index[node_id] = node
            for child in getattr(node, "children", []):
                _walk(child)

        _walk(scene)

    def _ensure_camera_binding(self):
        scene = self.engine.scene_manager.current_scene
        if scene is None:
            return

        camera = self._find_first_camera(scene)
        Node2D.camera = camera

    def _find_first_camera(self, node):
        if node.__class__.__name__ == "Camera2D":
            return node
        for child in getattr(node, "children", []):
            found = self._find_first_camera(child)
            if found is not None:
                return found
        return None


def main():
    host = EditorPreviewHost()
    host.start()


if __name__ == "__main__":
    main()
