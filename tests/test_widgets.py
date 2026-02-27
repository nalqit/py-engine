import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.pyengine2D.ui.ui_node import UINode
from src.pyengine2D.ui.widgets import UILabel, UIPanel, UIButton, UIProgressBar, UIListView
from src.pyengine2D.ui.event_system import UIEvent, UIMouseEvent


def test_ui_label():
    label = UILabel("Lbl", "Hello")
    assert label.text == "Hello"
    
    label.text = "World"
    assert label.text == "World"
    assert label.is_layout_dirty is True

def test_ui_button():
    btn = UIButton("Btn", "Click Me")
    assert btn.bg_color == btn.normal_color
    
    # Simulate hover
    btn.on_mouse_enter()
    assert btn.bg_color == btn.hover_color
    
    # Simulate mousedown
    event_down = UIMouseEvent(0, 0)
    btn.on_mouse_down(event_down)
    assert btn.bg_color == btn.pressed_color
    assert event_down.is_consumed is True
    
    # Simulate up
    event_up = UIMouseEvent(0, 0)
    btn.on_mouse_up(event_up)
    assert btn.bg_color == btn.hover_color
    
    # Simulate click
    clicked = []
    btn.get_signal("on_pressed").connect(lambda: clicked.append(True))
    
    event_click = UIMouseEvent(0, 0)
    btn.on_click(event_click)
    
    assert len(clicked) == 1
    assert event_click.is_consumed is True

def test_ui_progress_bar():
    pb = UIProgressBar("PB", 100, 20)
    assert pb.progress == 0.0
    
    pb.progress = 0.5
    assert pb.progress == 0.5
    
    pb.progress = 1.5
    assert pb.progress == 1.0 # Clamped
    
    pb.progress = -1.0
    assert pb.progress == 0.0 # Clamped

def test_ui_list_view_virtual_scrolling():
    # 100px tall list, 20px rows. Should create int(100/20) + 2 = 7 widgets
    lv = UIListView("List", width=200, height=100, row_height=20, item_class=UILabel)
    assert len(lv.row_widgets) == 7
    
    # Add 100 items
    items = [f"Item {i}" for i in range(100)]
    lv.set_items(items)
    assert lv.is_layout_dirty is True
    
    # Layout pass
    lv.perform_layout()
    
    # First widget should be "Item 0"
    assert lv.row_widgets[0].text == "Item 0"
    assert lv.row_widgets[0].local_y == 0
    
    # Scroll by 30 pixels (1.5 rows)
    lv.scroll(30)
    lv.perform_layout()
    
    # Start idx is 30 // 20 = 1. Offset is 30 % 20 = 10.
    # So first widget is bound to "Item 1" and y is 0 - 10 = -10
    assert lv.row_widgets[0].text == "Item 1"
    assert lv.row_widgets[0].local_y == -10
    
    # The 5th widget (index 4) is "Item 5"
    assert lv.row_widgets[4].text == "Item 5"

if __name__ == "__main__":
    test_ui_label()
    test_ui_button()
    test_ui_progress_bar()
    test_ui_list_view_virtual_scrolling()
    print("[PASS] test_widgets passed")
