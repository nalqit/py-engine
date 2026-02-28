from src.pyengine2D.scene.tilemap import TilemapNode

def test_tmx():
    tm = TilemapNode("Test")
    
    # We will trigger load_from_dict essentially via load_from_tmx
    # However it requires tileset assets so it will naturally print missing pygame image warnings
    # since dummy.png doesn't exist, but it should populate the arrays accurately.
    try:
        tm.load_from_tmx("test_map.tmx")
    except Exception as e:
        print("Exception caught while loading tmx:")
        print(e)
        return
        
    print("Map width:", tm.map_cols, "x", tm.map_rows)
    print("Tile dimensions:", tm.tile_width, "x", tm.tile_height)
    print("Number of parsed layers:", len(tm.layers))
    for layer in tm.layers:
        print(f" - Layer '{layer.get('name')}', solid: {layer.get('solid')}")

if __name__ == "__main__":
    test_tmx()
