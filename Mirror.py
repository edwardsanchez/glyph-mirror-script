# MenuTitle: Mirror Selection
# encoding: utf-8
"""
Mirror one edited half of a contour across a seam axis and replace the opposite half.
Only contours with selected nodes are touched, and the work happens on local copies
so other outlines remain untouched.
"""

from __future__ import division, print_function, unicode_literals

from GlyphsApp import Glyphs, Message, GSOFFCURVE
from vanilla import Window, Button, CheckBox, Group, RadioButton


SIDE_EPSILON = 0.5
SNAP_BAND = 5.0


class DirectionSelector(Group):
    """
    Small helper that lays out four radio buttons as a cross so the user can
    pick the side they edited. Only one option can be active at a time.
    """

    DIRECTIONS = [
        ("Top (mirror down)", "horizontal", "top"),
        ("Right (mirror left)", "vertical", "right"),
        ("Bottom (mirror up)", "horizontal", "bottom"),
        ("Left (mirror right)", "vertical", "left"),
    ]

    def __init__(self, posSize, default=3):
        super(DirectionSelector, self).__init__(posSize)
        self._buttons = []
        self._selected = default

        frames = [
            (80, 0, 200, 20),   # top
            (180, 36, 140, 20),  # right
            (80, 72, 200, 20),  # bottom
            (0, 36, 140, 20),   # left
        ]

        for index, ((title, _, _), frame) in enumerate(zip(self.DIRECTIONS, frames)):
            button = RadioButton(frame, title, callback=self._buttonCallback)
            button.set(index == default)
            setattr(self, "option_%d" % index, button)
            self._buttons.append(button)

    def _buttonCallback(self, sender):
        for index, button in enumerate(self._buttons):
            is_selected = button is sender
            button.set(is_selected)
            if is_selected:
                self._selected = index

    def get(self):
        return self._selected

    def set(self, index):
        if 0 <= index < len(self._buttons):
            self._selected = index
            for pos, button in enumerate(self._buttons):
                button.set(pos == index)


class MirrorSelectionUI(object):
    def __init__(self):
        font = Glyphs.font
        if not font or not font.selectedLayers:
            Message("No glyph selected", "Select a glyph and try again.")
            return

        self.font = font
        self.layer = font.selectedLayers[0]
        self._log_prefix = "[Mirror]"

        self.w = Window((360, 220), "Mirror Selection")
        self.w.direction = DirectionSelector((20, 20, 320, 100))
        self.w.snap = CheckBox(
            (20, 130, -20, 22),
            "Snap seam nodes to axis first",
            value=True,
        )
        self.w.runButton = Button(
            (20, 170, -20, 24),
            "Mirror",
            callback=self.runCallback,
        )
        self.w.open()

    def runCallback(self, sender):
        font = Glyphs.font
        if not font or not font.selectedLayers:
            Message("No glyph selected", "Select a glyph and try again.")
            return

        self.font = font
        self.layer = font.selectedLayers[0]

        direction_index = self.w.direction.get()
        _, axis, source_side = DirectionSelector.DIRECTIONS[direction_index]
        snap_first = bool(self.w.snap.get())

        self.log("Running mirror: axis=%s source=%s snap=%s" % (axis, source_side, snap_first))

        if self._mirrorSelection(axis, source_side, snap_first):
            if font.currentTab is not None:
                font.currentTab.redraw()
            self.w.close()

    def _mirrorSelection(self, axis, source_side, auto_snap):
        layer = self.layer
        selected_paths = []
        for idx, path in enumerate(layer.paths):
            if self._pathHasSelection(path):
                selected_paths.append((idx, path))

        if not selected_paths:
            Message("No nodes selected", "Select nodes on exactly one half of a contour and try again.")
            return False

        jobs = []
        for path_index, path in selected_paths:
            selected_nodes = [n for n in path.nodes if self._nodeIsSelectable(n) and n.selected]
            if not selected_nodes:
                continue

            seam = self._computeSeam(selected_nodes, axis, source_side)
            if not self._hasNodesOnSourceSide(selected_nodes, axis, source_side, seam):
                self.log("Path #%d: selection is seam-only" % path_index)
                Message(
                    "Selection is only seam nodes",
                    "Select the half you want to keep (not just the center line) and run again.",
                )
                return False

            if self._countSeamNodes(path, axis, seam) < 2:
                self.log("Path #%d: missing seam nodes near %.3f" % (path_index, seam))
                Message(
                    "Missing seam points",
                    "Select the seam nodes for each contour you want to mirror and try again.",
                )
                return False

            self.log(
                "Path #%d: selected=%d seam=%.3f"
                % (path_index, len(selected_nodes), seam)
            )
            jobs.append((path_index, path, seam))

        if not jobs:
            Message("No nodes selected", "Select nodes on one half of a contour and try again.")
            return False

        for path_index, path, seam in jobs:
            if not self._processPath(path_index, path, axis, source_side, seam, auto_snap):
                Message(
                    "Mirror failed",
                    "Could not rebuild one of the contours. Check your selection and try again.",
                )
                return False

        return True

    def _pathHasSelection(self, path):
        for node in path.nodes:
            if self._nodeIsSelectable(node) and node.selected:
                return True
        return False

    def _nodeIsSelectable(self, node):
        return node is not None and hasattr(node, "selected")

    def _computeSeam(self, nodes, axis, source_side):
        coords = [self._nodeCoord(node, axis) for node in nodes]
        if axis == "vertical":
            return max(coords) if source_side == "left" else min(coords)
        else:
            return min(coords) if source_side == "top" else max(coords)

    def _hasNodesOnSourceSide(self, nodes, axis, source_side, seam):
        for node in nodes:
            coord = self._nodeCoord(node, axis)
            if axis == "vertical":
                if source_side == "left" and coord < seam - SIDE_EPSILON:
                    return True
                if source_side == "right" and coord > seam + SIDE_EPSILON:
                    return True
            else:
                if source_side == "top" and coord > seam + SIDE_EPSILON:
                    return True
                if source_side == "bottom" and coord < seam - SIDE_EPSILON:
                    return True
        return False

    def _snapSeamNodes(self, selected_nodes, axis, seam):
        seam_nodes = []
        for node in selected_nodes:
            if node.type == GSOFFCURVE:
                continue
            delta = abs(self._nodeCoord(node, axis) - seam)
            if delta <= SNAP_BAND:
                seam_nodes.append(node)

        if not seam_nodes:
            return seam

        average = sum(self._nodeCoord(node, axis) for node in seam_nodes) / len(seam_nodes)
        for node in seam_nodes:
            self._setNodeCoord(node, axis, average)

        self.log(
            "Snapped %d seam nodes on working copy to %.3f (%s)"
            % (len(seam_nodes), average, axis)
        )

        return average

    def _processPath(self, path_index, path, axis, source_side, seam, auto_snap):
        working_path = path.copy()
        self.log("Path #%d: starting process (nodes=%d)" % (path_index, len(path.nodes)))

        if auto_snap:
            working_selected = [n for n in working_path.nodes if self._nodeIsSelectable(n) and n.selected]
            seam = self._snapSeamNodes(working_selected, axis, seam)
            self.log("Path #%d: snapped seam to %.3f" % (path_index, seam))

        source_half = self._trimOppositeSide(working_path, axis, source_side, seam)
        if not source_half.nodes:
            self.log("Path #%d: trim produced empty path" % path_index)
            return False

        unified_nodes = self._buildUnifiedNodes(path_index, source_half, axis, seam, source_side)
        if not unified_nodes:
            self.log("Path #%d: failed to build unified nodes" % path_index)
            return False

        self.log(
            "Path #%d: unified nodes=%d"
            % (path_index, len(unified_nodes))
        )

        unified_path = source_half.copy()
        unified_path.nodes = unified_nodes
        unified_path.closed = True
        self._writeBack(path, unified_path)
        return True

    def _trimOppositeSide(self, working_path, axis, source_side, seam):
        nodes_to_delete = []
        for index, node in enumerate(working_path.nodes):
            if not self._nodeIsSelectable(node):
                continue
            if node.selected:
                continue
            coord = self._nodeCoord(node, axis)
            if self._isOppositeCoord(coord, axis, source_side, seam):
                nodes_to_delete.append(index)

        for index in reversed(nodes_to_delete):
            del working_path.nodes[index]

        self.log(
            "Trimmed %d nodes on opposite side (%s/%s)"
            % (len(nodes_to_delete), axis, source_side)
        )

        return working_path

    def _countSeamNodes(self, path, axis, seam):
        count = 0
        for node in path.nodes:
            if self._isSeamOncurve(node, axis, seam):
                count += 1
        return count

    def _isOppositeCoord(self, coord, axis, source_side, seam):
        if abs(coord - seam) <= SIDE_EPSILON:
            return False

        if axis == "vertical":
            if source_side == "left":
                return coord > seam + SIDE_EPSILON
            return coord < seam - SIDE_EPSILON

        if source_side == "top":
            return coord < seam - SIDE_EPSILON
        return coord > seam + SIDE_EPSILON

    def _buildUnifiedNodes(self, path_index, source_half, axis, seam, source_side):
        mirrored_half = source_half.copy()
        mirrored_half.applyTransform(self._mirrorTransform(axis, seam))
        self.log("Path #%d: mirrored %d nodes" % (path_index, len(mirrored_half.nodes)))

        left_segment = self._extractSegment(
            path_index,
            source_half,
            axis,
            seam,
            expected_side=source_side,
            label="source",
        )
        mirror_side = self._oppositeSide(axis, source_side)
        right_segment = self._extractSegment(
            path_index,
            mirrored_half,
            axis,
            seam,
            expected_side=mirror_side,
            label="mirror",
        )

        if not left_segment or not right_segment:
            self.log("Path #%d: missing seam segments (left=%s right=%s)" % (path_index, bool(left_segment), bool(right_segment)))
            return None

        combined = list(left_segment)
        reversed_right = list(reversed(right_segment))
        if reversed_right:
            reversed_right = reversed_right[1:]
        combined.extend(reversed_right)
        combined = self._dedupeAdjacent(combined)
        self._snapNodeListToSeam(combined, axis, seam)
        if combined and self._nodesCoincide(combined[0], combined[-1]):
            combined.pop()
        return combined

    def _extractSegment(self, path_index, path, axis, seam, expected_side, label):
        nodes = list(path.nodes)
        count = len(nodes)
        if count == 0:
            return None

        seam_indices = [
            i for i, node in enumerate(nodes)
            if self._isSeamOncurve(node, axis, seam)
        ]
        if len(seam_indices) < 2:
            self.log("Path #%d: %s segment missing seam nodes (found %d)" % (path_index, label, len(seam_indices)))
            return None

        candidates = []
        for start_index in seam_indices:
            segment = []
            seam_hits = 0
            steps = 0
            idx = start_index
            while steps <= count:
                node_copy = nodes[idx].copy()
                segment.append(node_copy)
                if self._isSeamOncurve(node_copy, axis, seam):
                    seam_hits += 1
                    if seam_hits == 2 and steps > 0:
                        break
                idx = (idx + 1) % count
                steps += 1
            if seam_hits < 2:
                continue

            side_value = self._segmentSideValue(segment, axis, seam)
            matches = self._sideMatches(side_value, expected_side, axis, seam)
            candidates.append((segment, side_value, matches))

        if not candidates:
            self.log("Path #%d: %s segment missing seam pair" % (path_index, label))
            return None

        best = None
        best_len = -1
        fallback = None
        fallback_len = -1
        for segment, side_value, matches in candidates:
            seg_len = len(segment)
            if seg_len > fallback_len:
                fallback = segment
                fallback_len = seg_len
            if matches and seg_len > best_len:
                best = segment
                best_len = seg_len

        chosen = best if best is not None else fallback
        if chosen is None:
            return None

        chosen_matches = self._sideMatches(self._segmentSideValue(chosen, axis, seam), expected_side, axis, seam)
        self.log(
            "Path #%d: %s segment nodes=%d (matches=%s)"
            % (path_index, label, len(chosen), chosen_matches)
        )
        return chosen

    def _isSeamOncurve(self, node, axis, seam):
        if node.type == GSOFFCURVE:
            return False
        return abs(self._nodeCoord(node, axis) - seam) <= SNAP_BAND

    def _dedupeAdjacent(self, nodes):
        if not nodes:
            return []
        cleaned = [nodes[0]]
        for node in nodes[1:]:
            if self._nodesCoincide(cleaned[-1], node):
                continue
            cleaned.append(node)
        return cleaned

    def _segmentSideValue(self, segment, axis, seam):
        coords = []
        for node in segment:
            if node.type == GSOFFCURVE:
                continue
            coord = self._nodeCoord(node, axis)
            if abs(coord - seam) <= SIDE_EPSILON:
                continue
            coords.append(coord)
        if not coords:
            return None
        return sum(coords) / len(coords)

    def _sideMatches(self, side_value, expected_side, axis, seam):
        if expected_side is None or side_value is None:
            return False
        if axis == "vertical":
            if expected_side == "left":
                return side_value < seam - SIDE_EPSILON
            if expected_side == "right":
                return side_value > seam + SIDE_EPSILON
        else:
            if expected_side == "top":
                return side_value > seam + SIDE_EPSILON
            if expected_side == "bottom":
                return side_value < seam - SIDE_EPSILON
        return False

    def _oppositeSide(self, axis, side):
        if axis == "vertical":
            return "right" if side == "left" else "left"
        return "bottom" if side == "top" else "top"

    def _nodesCoincide(self, a, b, eps=0.01):
        return abs(a.x - b.x) <= eps and abs(a.y - b.y) <= eps

    def _snapNodeListToSeam(self, nodes, axis, seam):
        moved = 0
        for node in nodes:
            if node.type == GSOFFCURVE:
                continue
            if abs(self._nodeCoord(node, axis) - seam) <= SNAP_BAND:
                self._setNodeCoord(node, axis, seam)
                moved += 1
        self.log("Snapped %d nodes in combined path to seam %.3f" % (moved, seam))

    def _writeBack(self, target_path, source_path):
        target_path.nodes = [node.copy() for node in source_path.nodes]
        target_path.closed = source_path.closed
        for node in target_path.nodes:
            if self._nodeIsSelectable(node):
                node.selected = False

    def _nodeCoord(self, node, axis):
        return node.position.x if axis == "vertical" else node.position.y

    def _setNodeCoord(self, node, axis, value):
        if axis == "vertical":
            node.x = value
        else:
            node.y = value

    def _mirrorTransform(self, axis, seam):
        if axis == "vertical":
            return (-1.0, 0.0, 0.0, 1.0, 2.0 * seam, 0.0)
        return (1.0, 0.0, 0.0, -1.0, 0.0, 2.0 * seam)

    def log(self, message):
        print("%s %s" % (self._log_prefix, message))


def main():
    MirrorSelectionUI()


if __name__ == "__main__":
    main()
