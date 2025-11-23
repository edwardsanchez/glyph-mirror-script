# MenuTitle: Mirror Selection
# encoding: utf-8
"""
Mirror selected nodes across a seam axis.
Simple workflow: select one half of a contour, mirror it to replace the other half.
"""

from __future__ import division, print_function, unicode_literals
import objc
from GlyphsApp import Glyphs, Message, GSOFFCURVE, GSLayer
from vanilla import Window, RadioGroup, Button, CheckBox


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
    
    def runCallback(self, sender):
        """Execute the mirror operation based on UI selection."""
        index = self.w.sideRadio.get()
        autoSnap = bool(self.w.snapCheck.get())
        
        # index: 0 = Top, 1 = Right, 2 = Bottom, 3 = Left
        if index in (1, 3):
            # horizontal mirror (vertical seam)
            if index == 3:
                self.mirror(axis='vertical', sourceSide='left', autoSnap=autoSnap)
            else:
                self.mirror(axis='vertical', sourceSide='right', autoSnap=autoSnap)
        else:
            # vertical mirror (horizontal seam)
            if index == 0:
                self.mirror(axis='horizontal', sourceSide='top', autoSnap=autoSnap)
            else:
                self.mirror(axis='horizontal', sourceSide='bottom', autoSnap=autoSnap)
        
        self.font.currentTab.redraw()
        self.w.close()
    
    def mirror(self, axis='vertical', sourceSide='left', autoSnap=True):
        """
        Mirror selected nodes across a seam.
        
        axis: 'vertical' (left/right mirror) or 'horizontal' (top/bottom mirror)
        sourceSide: 'left', 'right', 'top', or 'bottom'
        """
        layer = self.layer
        
        # Find paths that have selected nodes
        selected_paths = []
        for path in layer.paths:
            if any(n.selected for n in path.nodes if n is not None):
                selected_paths.append(path)
        
        if not selected_paths:
            Message("No nodes selected", "Select nodes on one half of a contour and try again.")
            return
        
        print("[Mirror] Found %d paths with selected nodes" % len(selected_paths))
        
        # Process each selected path independently
        for path in selected_paths:
            self.mirrorPath(path, axis, sourceSide, autoSnap)
    
    def mirrorPath(self, path, axis, sourceSide, autoSnap):
        """Mirror a single path by replacing the opposite side with the selected side."""
        layer = self.layer

        # Collect selected nodes in this path
        selected_nodes = [n for n in path.nodes if n is not None and n.selected]
        
        if not selected_nodes:
            return
        
        # Determine seam axis from selected nodes
        if axis == 'vertical':
            # Vertical seam (left/right mirror)
            if sourceSide == 'left':
                seam_coord = max(n.position.x for n in selected_nodes)
            else:  # right
                seam_coord = min(n.position.x for n in selected_nodes)
            coord_attr = 'x'
        else:
            # Horizontal seam (top/bottom mirror)
            if sourceSide == 'top':
                seam_coord = min(n.position.y for n in selected_nodes)
            else:  # bottom
                seam_coord = max(n.position.y for n in selected_nodes)
            coord_attr = 'y'
        
        print("[Mirror] Path seam at %s=%.1f" % (coord_attr, seam_coord))

        # Guard: ensure we actually have some nodes clearly on one side of the seam.
        # If the user only selected the seam nodes, do NOTHING instead of destroying the path.
        side_nodes = []
        for n in selected_nodes:
            v = getattr(n.position, coord_attr)
            if axis == 'vertical':
                if sourceSide == 'left' and v < seam_coord - 0.01:
                    side_nodes.append(n)
                elif sourceSide == 'right' and v > seam_coord + 0.01:
                    side_nodes.append(n)
            else:
                if sourceSide == 'top' and v > seam_coord + 0.01:
                    side_nodes.append(n)
                elif sourceSide == 'bottom' and v < seam_coord - 0.01:
                    side_nodes.append(n)

        if not side_nodes:
            # Only seam (or nearly-seam) nodes selected – bail out safely.
            Message(
                "Selection is only seam nodes",
                "Select the half you want to keep (not just the center line) and run again."
            )
            print("[Mirror] Aborted: selection contained only seam nodes")
            return
        
        # Snap seam nodes if requested
        if autoSnap:
            seam_nodes = [n for n in selected_nodes 
                         if n.type != GSOFFCURVE 
                         and abs(getattr(n.position, coord_attr) - seam_coord) <= 5.0]
            
            if seam_nodes:
                avg = sum(getattr(n.position, coord_attr) for n in seam_nodes) / len(seam_nodes)
                for n in seam_nodes:
                    setattr(n.position, coord_attr, avg)
                seam_coord = avg
                print("[Mirror] Snapped %d seam nodes to %.1f" % (len(seam_nodes), avg))
        
        # Work on a copy of the path so we can replace the original cleanly
        try:
            pathIndex = list(layer.paths).index(path)
        except ValueError:
            # Path not found in layer; nothing to do
            print("[Mirror] Warning: path not found in layer")
            return

        working_path = path.copy()

        # Delete nodes on the opposite side (unselected nodes beyond the seam),
        # but only within this working copy.
        to_delete = []
        for i, node in enumerate(working_path.nodes):
            if node is None or node.selected:
                continue
            
            node_coord = getattr(node.position, coord_attr)
            
            # Check if node is on opposite side of seam
            if axis == 'vertical':
                if sourceSide == 'left' and node_coord > seam_coord + 0.01:
                    to_delete.append(i)
                elif sourceSide == 'right' and node_coord < seam_coord - 0.01:
                    to_delete.append(i)
            else:
                if sourceSide == 'top' and node_coord < seam_coord - 0.01:
                    to_delete.append(i)
                elif sourceSide == 'bottom' and node_coord > seam_coord + 0.01:
                    to_delete.append(i)
        
        # Delete in reverse order to maintain indices
        for i in reversed(to_delete):
            del working_path.nodes[i]

        print("[Mirror] Deleted %d nodes on opposite side" % len(to_delete))
        
        # Now mirror the remaining (source) side
        source_half = working_path
        mirrored_half = source_half.copy()
        
        # Apply mirror transform
        if axis == 'vertical':
            # Mirror horizontally: x' = -x + 2*seam
            mirrored_half.applyTransform((-1.0, 0.0, 0.0, 1.0, 2.0 * seam_coord, 0.0))
        else:
            # Mirror vertically: y' = -y + 2*seam
            mirrored_half.applyTransform((1.0, 0.0, 0.0, -1.0, 0.0, 2.0 * seam_coord))

        # Build a temporary layer containing just the two halves and remove overlap there
        tmp_layer = GSLayer()
        tmp_layer.width = layer.width
        tmp_layer.paths.append(source_half)
        tmp_layer.paths.append(mirrored_half)
        tmp_layer.removeOverlap()

        if not tmp_layer.paths:
            print("[Mirror] Warning: no paths produced after removeOverlap()")
            return

        # Take the first resulting path as the unified outline and copy its nodes
        unified = tmp_layer.paths[0]
        # Replace nodes of the original path IN PLACE (don't touch layer.paths container)
        path.nodes = [n.copy() for n in unified.nodes]
        path.closed = unified.closed

        print("[Mirror] Updated original path with unified mirrored outline")


def main():
    MirrorSelectionUI()


if __name__ == "__main__":
    main()
