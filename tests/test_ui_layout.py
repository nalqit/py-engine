import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.pyengine2D.scene.node2d import Node2D
from src.pyengine2D.ui.ui_node import UINode, Anchor, SizePolicy
from src.pyengine2D.ui.containers import VBoxContainer, HBoxContainer, GridContainer


def test_ui_node_anchoring():
    parent = UINode("Parent", 500, 500)
    child = UINode("Child", 100, 100)
    parent.add_child(child)
    
    # 1. Top Left (Default)
    child.anchor = Anchor.TOP_LEFT
    child.margin_left = 10
    child.margin_top = 20
    parent.update(0) # Triggers layout
    
    print(f"Child local: {child.local_x}, {child.local_y}")
    assert child.local_x == 10
    assert child.local_y == 20
    
    # 2. Bottom Right
    child.anchor = Anchor.BOTTOM_RIGHT
    child.margin_right = 10
    child.margin_bottom = 20
    child.mark_layout_dirty()
    parent.update(0)
    
    assert child.local_x == 500 - 100 - 10 # 390
    assert child.local_y == 500 - 100 - 20 # 380
    
    # 3. Center
    child.anchor = Anchor.CENTER
    child.margin_left = 0
    child.margin_top = 0
    child.mark_layout_dirty()
    parent.update(0)
    
    assert child.local_x == 200 # (500/2) - (100/2)
    assert child.local_y == 200


def test_vbox_container_wrap():
    vbox = VBoxContainer("VBox")
    vbox.spacing = 10
    
    c1 = UINode("C1", width=100, height=50)
    c2 = UINode("C2", width=120, height=30)
    
    vbox.add_child(c1)
    vbox.add_child(c2)
    
    vbox.update(0)
    
    # Check positions
    assert c1.local_y == 0
    assert c2.local_y == 50 + 10 # 60
    
    # Check dynamic size wrap
    assert vbox.width == 120 # max child width
    assert vbox.height == 50 + 10 + 30 # sum heights + spacing = 90


def test_hbox_container_fill():
    parent = UINode("Parent", 1000, 100)
    
    hbox = HBoxContainer("HBox")
    hbox.spacing = 0
    hbox.size_policy_x = SizePolicy.FILL # Fill the 1000px parent
    hbox.size_policy_y = SizePolicy.FILL
    
    parent.add_child(hbox)
    
    c1 = UINode("C1", width=200, height=50)
    # c2 should fill remaining horizontal space if it was supported, 
    # but the current containers only support FILL on the orthogonal axis (e.g., FILL Y inside HBox).
    # Let's test FILL Y inside HBox
    c1.size_policy_y = SizePolicy.FILL
    
    hbox.add_child(c1)
    parent.update(0) # Propagates down
    
    assert hbox.width == 1000
    assert hbox.height == 100
    assert c1.height == 100 # Filled to HBox height


if __name__ == "__main__":
    test_ui_node_anchoring()
    test_vbox_container_wrap()
    test_hbox_container_fill()
    print("[PASS] All UI Layout tests passed")
