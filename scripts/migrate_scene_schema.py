import argparse
import json
from pathlib import Path


META_KEYS = {"id", "name", "type", "children", "script", "_original_type"}


def to_properties_node(node):
    if not isinstance(node, dict):
        return node

    node = dict(node)
    properties = node.get("properties")

    if not isinstance(properties, dict):
        properties = {}
        for key in list(node.keys()):
            if key in META_KEYS:
                continue
            properties[key] = node.pop(key)
        node["properties"] = properties

    children = node.get("children", [])
    if isinstance(children, list):
        node["children"] = [to_properties_node(child) for child in children]

    return node


def migrate_file(scene_path):
    with scene_path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    migrated = to_properties_node(data)

    with scene_path.open("w", encoding="utf-8") as f:
        json.dump(migrated, f, indent=2, ensure_ascii=False)
        f.write("\n")


def main():
    parser = argparse.ArgumentParser(description="Migrate .scene files to properties schema")
    parser.add_argument("paths", nargs="+", help="Scene files or directories")
    args = parser.parse_args()

    migrated_count = 0
    for raw_path in args.paths:
        path = Path(raw_path)
        if path.is_file() and path.suffix == ".scene":
            migrate_file(path)
            migrated_count += 1
            continue

        if path.is_dir():
            for scene_path in path.rglob("*.scene"):
                migrate_file(scene_path)
                migrated_count += 1

    print(f"Migrated {migrated_count} scene file(s).")


if __name__ == "__main__":
    main()
