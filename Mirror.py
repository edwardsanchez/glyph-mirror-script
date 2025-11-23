# MenuTitle: Mirror Selection
# encoding: utf-8
"""
Mirror selected glyph nodes across a seam axis.
Supports horizontal (left/right) and vertical (top/bottom) mirroring
with strict seam validation and optional auto-snapping.
"""

from __future__ import division, print_function, unicode_literals
import objc
from GlyphsApp import Glyphs, Message, GSOFFCURVE
from vanilla import Window, RadioGroup, Button, CheckBox

# Import the pure Python mirror geometry module
import sys
import os
script_dir = os.path.dirname(os.path.abspath(__file__))
if script_dir not in sys.path:
    sys.path.insert(0, script_dir)

from mirror_geometry import Point, mirror_horizontal, mirror_vertical, MirrorError


def log(message):
    """Log helper to Macro Panel."""
    try:
        print("[Mirror] %s" % message)
    except Exception:
        pass


class MirrorSelectionUI(object):
    def __init__(self):
        self.font = Glyphs.font
        if not self.font or not self.font.selectedLayers:
            Message("No glyph selected", "Select a glyph and try again.")
            return
        
        self.layer = self.font.selectedLayers[0]
        
        # Build window
        self.w = Window((280, 180), "Mirror Selection")
        
        self.w.sideRadio = RadioGroup(
            (10, 10, -10, 80),
            [
                "Top (mirror down)",
                "Right (mirror left)",
                "Bottom (mirror up)",
                "Left (mirror right)",
            ],
            isVertical=True,
        )
        self.w.sideRadio.set(3)  # default: Left
        
        self.w.snapCheck = CheckBox(
            (10, 100, -10, 20),
            "Snap seam nodes to axis first",
            value=True,
        )
        
        self.w.runButton = Button(
            (10, 140, -10, 20),
            "Mirror",
            callback=self.runCallback,
        )
        
        self.w.open()
    
    def selectedNodes(self):
        """Collect all selected nodes from the layer."""
        return [n for p in self.layer.paths for n in p.nodes if n.selected]

    def _collect_horizontal_seam_nodes(self, selNodes, axisX, center_band):
        """Ensure seam nodes exist near axisX. Returns (seam_nodes, updated_selection)."""
        seam_nodes = [
            n for n in selNodes
            if n.type != GSOFFCURVE and abs(n.position.x - axisX) <= center_band
        ]
        if seam_nodes:
            return seam_nodes, selNodes

        auto_nodes = []
        for path in self.layer.paths:
            for node in path.nodes:
                if (
                    node is not None
                    and node.type != GSOFFCURVE
                    and abs(node.position.x - axisX) <= center_band
                ):
                    node.selected = True
                    auto_nodes.append(node)

        if auto_nodes:
            log("Auto-selected %d seam nodes near x=%.3f" % (len(auto_nodes), axisX))
            new_selection = self.selectedNodes()
            seam_nodes = [
                n for n in new_selection
                if n.type != GSOFFCURVE and abs(n.position.x - axisX) <= center_band
            ]
            return seam_nodes, new_selection

        return [], selNodes

    def _collect_vertical_seam_nodes(self, selNodes, axisY, center_band):
        """Ensure seam nodes exist near axisY. Returns (seam_nodes, updated_selection)."""
        seam_nodes = [
            n for n in selNodes
            if n.type != GSOFFCURVE and abs(n.position.y - axisY) <= center_band
        ]
        if seam_nodes:
            return seam_nodes, selNodes

        auto_nodes = []
        for path in self.layer.paths:
            for node in path.nodes:
                if (
                    node is not None
                    and node.type != GSOFFCURVE
                    and abs(node.position.y - axisY) <= center_band
                ):
                    node.selected = True
                    auto_nodes.append(node)

        if auto_nodes:
            log("Auto-selected %d seam nodes near y=%.3f" % (len(auto_nodes), axisY))
            new_selection = self.selectedNodes()
            seam_nodes = [
                n for n in new_selection
                if n.type != GSOFFCURVE and abs(n.position.y - axisY) <= center_band
            ]
            return seam_nodes, new_selection

        return [], selNodes
    
    def runCallback(self, sender):
        """Execute the mirror operation based on UI selection."""
        index = self.w.sideRadio.get()
        autoSnap = bool(self.w.snapCheck.get())
        
        # index: 0 = Top, 1 = Right, 2 = Bottom, 3 = Left
        if index in (1, 3):
            # horizontal mirror (vertical seam)
            if index == 3:
                self.mirrorHorizontal(sourceSide="left", autoSnap=autoSnap)
            else:
                self.mirrorHorizontal(sourceSide="right", autoSnap=autoSnap)
        else:
            # vertical mirror (horizontal seam)
            if index == 0:
                self.mirrorVertical(sourceSide="top", autoSnap=autoSnap)
            else:
                self.mirrorVertical(sourceSide="bottom", autoSnap=autoSnap)
        
        self.font.currentTab.redraw()
        self.w.close()
    
    def mirrorHorizontal(self, sourceSide="left", autoSnap=True):
        """
        Mirror horizontally: seam is a vertical line (constant x).
        sourceSide: "left" or "right"
        """
        layer = self.layer
        paths = layer.paths
        selNodes = self.selectedNodes()
        log("Vertical mirror: %s source, %d selected nodes" % (sourceSide, len(selNodes)))
        log("Horizontal mirror: %s source, %d selected nodes" % (sourceSide, len(selNodes)))
        
        if not selNodes:
            Message(
                "No nodes selected",
                "Select one half plus all seam points, then run again."
            )
            return
        
        # Decide seam x based on source side
        if sourceSide == "left":
            axisX = max(n.position.x for n in selNodes)  # right edge of selected half
        else:
            axisX = min(n.position.x for n in selNodes)  # left edge of selected half
        log("Initial axisX: %.3f" % axisX)
        
        center_band = 5.0
        eps = 0.01
        
        # Convert GSNode to Point for geometry module
        points = []
        for node in selNodes:
            on_curve = (node.type != GSOFFCURVE)
            points.append(Point(node.position.x, node.position.y, on_curve))
        
        seam_nodes, selNodes = self._collect_horizontal_seam_nodes(selNodes, axisX, center_band)
        if not seam_nodes:
            Message(
                "No seam points found",
                f"Could not find seam nodes near x={axisX:.1f}. Select the seam line and try again."
            )
            return

        # If auto-snap enabled, snap all on-curve nodes in seam band
        if autoSnap:
            avg_x = sum(n.position.x for n in seam_nodes) / len(seam_nodes)
            for path in paths:
                for node in path.nodes:
                    if (
                        node is not None
                        and node.type != GSOFFCURVE
                        and abs(node.position.x - axisX) <= center_band
                    ):
                        node.position.x = avg_x
            axisX = avg_x
            log("Axis snapped to %.3f" % axisX)
            # Re-evaluate seam nodes after snapping
            seam_nodes, selNodes = self._collect_horizontal_seam_nodes(selNodes, axisX, center_band)
            if not seam_nodes:
                Message(
                    "No seam points found",
                    f"Could not find seam nodes near snapped x={axisX:.1f}. Select the seam line and try again."
                )
                return
            log("Axis snapped to %.3f" % axisX)
        
        # Validate seam alignment using geometry module
        try:
            # Re-collect points after potential snapping
            points = []
            for node in selNodes:
                on_curve = (node.type != GSOFFCURVE)
                points.append(Point(node.position.x, node.position.y, on_curve))
            
            # This will validate the seam
            from mirror_geometry import find_seam_points, validate_seam_alignment
            seam_points = find_seam_points(points, axisX, center_band, check_x=True)
            
            if not seam_points:
                Message(
                    "No seam points found",
                    f"Could not find selected seam nodes near x={axisX:.1f}.\n"
                    "Select the seam line and try again."
                )
                return
            
            aligned_x = validate_seam_alignment(seam_points, check_x=True, eps=eps)
            axisX = aligned_x
            log("Aligned axisX: %.3f" % axisX)
            
        except MirrorError as e:
            Message(
                "Seam validation failed",
                str(e) + "\n\nAlign seam points or enable snapping, then run again."
            )
            return
        
        # Relaxed check: only verify selected seam nodes are aligned
        # We no longer require ALL seam nodes to be selected - unselected ones on the
        # opposite side will be deleted anyway. This supports the "update existing shape" workflow.
        
        # Record which paths had selections before we start deleting nodes.
        # (Deleting nodes can clear the selection internally in Glyphs.)
        paths_with_selection = [p for p in paths if any(n.selected for n in p.nodes)]
        log("Paths with selection (before deletion): %d" % len(paths_with_selection))
        if not paths_with_selection:
            Message(
                "No nodes selected",
                "Select the half you want to keep (including seam nodes) and try again."
            )
            return

        # Remove unselected nodes on the opposite side
        deleted_counts = 0
        for path in paths:
            if not any(n.selected for n in path.nodes):
                continue
            
            to_delete = []
            for i, node in enumerate(path.nodes):
                if not node.selected:
                    if sourceSide == "left":
                        # delete right side
                        if node.position.x > axisX + eps:
                            to_delete.append(i)
                    else:
                        # delete left side
                        if node.position.x < axisX - eps:
                            to_delete.append(i)
            
            for i in reversed(to_delete):
                del path.nodes[i]
            deleted_counts += len(to_delete)
        log("Deleted %d nodes on opposite side" % deleted_counts)
        
        # Duplicate and mirror selected paths
        paths_to_mirror = paths_with_selection
        new_paths = []
        
        for p in paths_to_mirror:
            new_path = p.copy()
            # Mirror horizontally: x' = -x + 2*axisX
            new_path.applyTransform((-1.0, 0.0, 0.0, 1.0, 2.0 * axisX, 0.0))
            for n in new_path.nodes:
                if n is not None:
                    n.selected = False
            new_paths.append(new_path)
        log("Created %d mirrored paths" % len(new_paths))
        
        for p in new_paths:
            layer.paths.append(p)
        log("Layer now has %d paths" % len(layer.paths))
        
        layer.removeOverlap()
        layer.correctPathDirection()
    
    def mirrorVertical(self, sourceSide="top", autoSnap=True):
        """
        Mirror vertically: seam is a horizontal line (constant y).
        sourceSide: "top" or "bottom"
        """
        layer = self.layer
        paths = layer.paths
        selNodes = self.selectedNodes()
        
        if not selNodes:
            Message(
                "No nodes selected",
                "Select one half plus all seam points, then run again."
            )
            return
        
        # Decide seam y based on source side
        # Note: In Glyphs, y increases upward, so top has larger y
        if sourceSide == "top":
            axisY = min(n.position.y for n in selNodes)  # bottom edge of top half
        else:
            axisY = max(n.position.y for n in selNodes)  # top edge of bottom half
        log("Initial axisY: %.3f" % axisY)
        
        center_band = 5.0
        eps = 0.01
        
        # Convert GSNode to Point for geometry module
        points = []
        for node in selNodes:
            on_curve = (node.type != GSOFFCURVE)
            points.append(Point(node.position.x, node.position.y, on_curve))
        
        seam_nodes, selNodes = self._collect_vertical_seam_nodes(selNodes, axisY, center_band)
        if not seam_nodes:
            Message(
                "No seam points found",
                f"Could not find seam nodes near y={axisY:.1f}. Select the seam line and try again."
            )
            return

        # If auto-snap enabled, snap all on-curve nodes in seam band
        if autoSnap:
            avg_y = sum(n.position.y for n in seam_nodes) / len(seam_nodes)
            for path in paths:
                for node in path.nodes:
                    if (
                        node is not None
                        and node.type != GSOFFCURVE
                        and abs(node.position.y - axisY) <= center_band
                    ):
                        node.position.y = avg_y
            axisY = avg_y
            log("Axis snapped to %.3f" % axisY)
            seam_nodes, selNodes = self._collect_vertical_seam_nodes(selNodes, axisY, center_band)
            if not seam_nodes:
                Message(
                    "No seam points found",
                    f"Could not find seam nodes near snapped y={axisY:.1f}. Select the seam line and try again."
                )
                return
            log("Axis snapped to %.3f" % axisY)
        
        # Validate seam alignment
        try:
            points = []
            for node in selNodes:
                on_curve = (node.type != GSOFFCURVE)
                points.append(Point(node.position.x, node.position.y, on_curve))
            
            from mirror_geometry import find_seam_points, validate_seam_alignment
            seam_points = find_seam_points(points, axisY, center_band, check_x=False)
            
            if not seam_points:
                Message(
                    "No seam points found",
                    f"Could not find selected seam nodes near y={axisY:.1f}.\n"
                    "Select the seam line and try again."
                )
                return
            
            aligned_y = validate_seam_alignment(seam_points, check_x=False, eps=eps)
            axisY = aligned_y
            log("Aligned axisY: %.3f" % axisY)
            
        except MirrorError as e:
            Message(
                "Seam validation failed",
                str(e) + "\n\nAlign seam points or enable snapping, then run again."
            )
            return
        
        # Relaxed check: only verify selected seam nodes are aligned
        # We no longer require ALL seam nodes to be selected - unselected ones on the
        # opposite side will be deleted anyway. This supports the "update existing shape" workflow.
        
        # Record paths that had selected nodes before deletion.
        paths_with_selection = [p for p in paths if any(n.selected for n in p.nodes)]
        log("Paths with selection (before deletion): %d" % len(paths_with_selection))
        if not paths_with_selection:
            Message(
                "No nodes selected",
                "Select the half you want to keep (including seam nodes) and try again."
            )
            return

        # Remove unselected nodes on opposite side
        deleted_counts = 0
        for path in paths:
            if not any(n.selected for n in path.nodes):
                continue
            
            to_delete = []
            for i, node in enumerate(path.nodes):
                if not node.selected:
                    if sourceSide == "top":
                        # delete below seam
                        if node.position.y < axisY - eps:
                            to_delete.append(i)
                    else:
                        # delete above seam
                        if node.position.y > axisY + eps:
                            to_delete.append(i)
            
            for i in reversed(to_delete):
                del path.nodes[i]
            deleted_counts += len(to_delete)
        log("Deleted %d nodes on opposite side" % deleted_counts)
        
        # Duplicate and mirror selected paths
        paths_to_mirror = paths_with_selection
        new_paths = []
        
        for p in paths_to_mirror:
            new_path = p.copy()
            # Mirror vertically: y' = -y + 2*axisY
            new_path.applyTransform((1.0, 0.0, 0.0, -1.0, 0.0, 2.0 * axisY))
            for n in new_path.nodes:
                if n is not None:
                    n.selected = False
            new_paths.append(new_path)
        log("Created %d mirrored paths" % len(new_paths))
        
        for p in new_paths:
            layer.paths.append(p)
        log("Layer now has %d paths" % len(layer.paths))
        
        layer.removeOverlap()
        layer.correctPathDirection()


def main():
    MirrorSelectionUI()


if __name__ == "__main__":
    main()

