# MenuTitle: Mirror Selection
# encoding: utf-8
"""
Mirror selected nodes across a seam axis.
Simple workflow: select one half of a contour, mirror it to replace the other half.
"""

from __future__ import division, print_function, unicode_literals
import objc
from GlyphsApp import Glyphs, Message, GSOFFCURVE, GSLayer, GSPath
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
        
        if self.font.currentTab:
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
        
        # Calculate the TRUE center from total path bounds
        all_nodes = [n for n in path.nodes if n is not None]
        if axis == 'vertical':
            min_coord = min(n.position.x for n in all_nodes)
            max_coord = max(n.position.x for n in all_nodes)
        else:
            min_coord = min(n.position.y for n in all_nodes)
            max_coord = max(n.position.y for n in all_nodes)
        bounds_center = (min_coord + max_coord) / 2.0
        original_size = max_coord - min_coord
        
        print("[Mirror] Total path bounds %s: [%.1f, %.1f], center: %.1f, size: %.1f" % 
              (coord_attr, min_coord, max_coord, bounds_center, original_size))
        print("[Mirror] Selection edge seam at %s=%.1f" % (coord_attr, seam_coord))
        
        # Check if selected nodes actually reach the TRUE center (bounds center)
        # If not, use bounds center as the axis instead of selection edge
        seam_band = 5.0
        nodes_at_center = [n for n in selected_nodes 
                          if n.type != GSOFFCURVE 
                          and abs(getattr(n.position, coord_attr) - bounds_center) <= seam_band]
        
        if not nodes_at_center:
            # Selection doesn't reach center - use bounds center as axis
            seam_coord = bounds_center
            print("[Mirror] Selection doesn't reach center, using bounds center: %s=%.1f" % (coord_attr, seam_coord))
        else:
            print("[Mirror] Found %d nodes at center, using seam-based axis" % len(nodes_at_center))

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
            
        # If we deleted nodes, the path should be open for merging
        if to_delete:
            working_path.closed = False

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

        # Log initial metrics
        print("[Mirror] Source half: %d nodes, closed=%s" % (len(source_half.nodes), source_half.closed))
        print("[Mirror] Mirrored half: %d nodes, closed=%s" % (len(mirrored_half.nodes), mirrored_half.closed))
        
        # Calculate expected final node count
        selected_count = len(selected_nodes)
        
        # Count how many nodes in the source_half are on the seam (will be deduplicated)
        seam_node_count = sum(1 for n in source_half.nodes 
                             if abs(getattr(n.position, coord_attr) - seam_coord) <= 1.0)
        
        # Expected = source + mirrored - seam_duplicates
        expected_count = len(source_half.nodes) + len(mirrored_half.nodes) - seam_node_count
        
        print("[Mirror] Selected: %d, source half: %d, seam nodes to dedupe: %d, expected final: %d" % 
              (selected_count, len(source_half.nodes), seam_node_count, expected_count))
        
        # Try removeOverlap first
        tmp_layer = GSLayer()
        tmp_layer.width = layer.width
        tmp_layer.paths.append(source_half)
        tmp_layer.paths.append(mirrored_half)
        tmp_layer.removeOverlap()
        
        print("[Mirror] After removeOverlap: %d paths" % len(tmp_layer.paths))
        
        # If removeOverlap didn't merge (still 2 paths), manually merge them
        if len(tmp_layer.paths) >= 2:
            print("[Mirror] removeOverlap didn't merge, manually combining paths...")
            
            # Reverse the mirrored path using Glyphs API to preserve Bezier structure
            mirrored_half.reverse()
            
            # Manual merge logic for open paths forming a closed shape
            # Source: A -> ... -> B
            # Mirror (Reversed): B' -> ... -> A'
            
            seam_tolerance = 1.0
            unified_nodes = []
            
            # Add all source nodes
            for n in source_half.nodes:
                unified_nodes.append(n.copy())
            
            # Add mirrored nodes (already reversed), skipping seam duplicates
            for n in mirrored_half.nodes:
                node_coord = getattr(n.position, coord_attr)
                is_seam_node = abs(node_coord - seam_coord) <= seam_tolerance
                
                # Check for duplicate against last added node (B -> B')
                if unified_nodes:
                    last = unified_nodes[-1]
                    if (abs(n.position.x - last.position.x) < 0.1 and 
                        abs(n.position.y - last.position.y) < 0.1):
                        continue
                
                # Check for duplicate against first node (A' -> A) - only if near seam
                if is_seam_node and unified_nodes:
                    first = unified_nodes[0]
                    if (abs(n.position.x - first.position.x) < 0.1 and 
                        abs(n.position.y - first.position.y) < 0.1):
                        continue
                
                unified_nodes.append(n.copy())
            
            # Create the unified path
            unified = GSPath()
            for n in unified_nodes:
                unified.nodes.append(n)
            unified.closed = True
            
            print("[Mirror] Manually merged: %d nodes" % len(unified.nodes))
        else:
            unified = tmp_layer.paths[0]
            print("[Mirror] removeOverlap merged successfully: %d nodes" % len(unified.nodes))

        if not unified or len(unified.nodes) == 0:
            print("[Mirror] Warning: no nodes in unified path")
            return

        # Calculate final bounds and verify size is maintained
        final_nodes = list(unified.nodes)
        if final_nodes:
            if axis == 'vertical':
                final_min = min(n.position.x for n in final_nodes)
                final_max = max(n.position.x for n in final_nodes)
            else:
                final_min = min(n.position.y for n in final_nodes)
                final_max = max(n.position.y for n in final_nodes)
            final_size = final_max - final_min
            
            print("[Mirror] Final bounds %s: [%.1f, %.1f], size: %.1f" % 
                  (coord_attr, final_min, final_max, final_size))
            
            # Check if size is maintained
            if abs(final_size - original_size) > 1.0:
                print("[Mirror] WARNING: Size changed! Original: %.1f, Final: %.1f" % 
                      (original_size, final_size))
        
        # Replace nodes of the original path IN PLACE
        path.nodes = [n.copy() for n in unified.nodes]
        path.closed = unified.closed
        
        print("[Mirror] Final path: %d nodes (expected: %d)" % (len(path.nodes), expected_count))


def main():
    MirrorSelectionUI()


if __name__ == "__main__":
    main()
