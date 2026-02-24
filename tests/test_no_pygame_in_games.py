"""
Import Guard Test — Phase 0 Enforcement
Scans all files under src/game/ and src/games/ for direct 'import pygame' usage.
Game and benchmark code must NEVER touch pygame directly.
"""
import os
import sys
import ast

# Project root
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

GAME_DIRS = [
    os.path.join(ROOT, "src", "game"),
    os.path.join(ROOT, "src", "games"),
]

# These directories are allowed to import pygame (engine internals)
ALLOWED_DIRS = [
    os.path.join(ROOT, "src", "engine"),
]


def _collect_python_files(directory):
    """Yield all .py files recursively under directory."""
    if not os.path.isdir(directory):
        return
    for dirpath, _, filenames in os.walk(directory):
        for fn in filenames:
            if fn.endswith(".py"):
                yield os.path.join(dirpath, fn)


def _check_file_for_pygame_import(filepath):
    """Return list of line numbers where 'import pygame' or 'from pygame' appears."""
    violations = []
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            tree = ast.parse(f.read(), filename=filepath)
    except SyntaxError:
        return violations

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == "pygame" or alias.name.startswith("pygame."):
                    violations.append(node.lineno)
        elif isinstance(node, ast.ImportFrom):
            if node.module and (node.module == "pygame" or node.module.startswith("pygame.")):
                violations.append(node.lineno)
    return violations


def test_no_pygame_in_games():
    """Ensure no game or benchmark file imports pygame directly."""
    all_violations = []

    for game_dir in GAME_DIRS:
        for filepath in _collect_python_files(game_dir):
            lines = _check_file_for_pygame_import(filepath)
            if lines:
                relpath = os.path.relpath(filepath, ROOT)
                all_violations.append((relpath, lines))

    if all_violations:
        msg_parts = ["PYGAME IMPORT VIOLATIONS DETECTED:"]
        for path, lines in all_violations:
            msg_parts.append(f"  {path}: lines {lines}")
        raise AssertionError("\n".join(msg_parts))

    print("[PASS] test_no_pygame_in_games — no violations found")


def test_engine_files_use_renderer():
    """
    Verify that engine UI files do NOT use raw pygame draw/font calls.
    They should route through Engine.instance.renderer.
    """
    ui_dir = os.path.join(ROOT, "src", "engine", "ui")
    violations = []

    for filepath in _collect_python_files(ui_dir):
        basename = os.path.basename(filepath)
        lines = _check_file_for_pygame_import(filepath)
        if lines:
            relpath = os.path.relpath(filepath, ROOT)
            violations.append((relpath, lines))

    if violations:
        msg_parts = ["ENGINE UI FILES STILL IMPORT PYGAME DIRECTLY:"]
        for path, lines in violations:
            msg_parts.append(f"  {path}: lines {lines}")
        raise AssertionError("\n".join(msg_parts))

    print("[PASS] test_engine_files_use_renderer — UI files are clean")


if __name__ == "__main__":
    test_no_pygame_in_games()
    test_engine_files_use_renderer()
