# Glyphs Scripting: Lessons Learned for AI Agents

This document records technical challenges and solutions discovered while developing Glyphs 3 scripts, specifically for geometry manipulation and mirroring.

## 1. Path Manipulation & Mirroring

### ❌ What Doesn't Work

*   **Manually reversing node lists**: `list(reversed(path.nodes))` destroys Bézier curve structure. A curve segment `P1 -> H1 -> H2 -> P2` becomes `P2 -> H2 -> H1 -> P1` in the list, but Glyphs expects the node types to match the position in the segment (Line/Curve at end, OffCurves before it).
*   **Modifying paths in-place for mirroring**: Deleting nodes from a path and then trying to mirror it often leads to lost data or broken closed/open states.
*   **`removeOverlap()` on adjacent paths**: Glyphs' `removeOverlap` works great for intersecting shapes, but can fail to merge paths that merely "touch" at a seam (share an edge). It treats them as separate contours.
*   **`del layer.paths[i]` inside a loop**: Modifying the container you are iterating over causes index errors.
*   **Assuming `path.closed` updates automatically**: When you delete nodes from a closed path to make it an open segment, you must explicitly set `path.closed = False`.

### ✅ What Works (The "Golden Path")

1.  **Work on Copies**: Always `.copy()` the path before modification.
    ```python
    working_path = path.copy()
    ```
2.  **Use Affine Transforms**: Don't calculate coordinates manually if you can use a matrix.
    ```python
    # Mirror horizontally around x=axis
    transform = (-1.0, 0.0, 0.0, 1.0, 2.0 * axis, 0.0)
    path.applyTransform(transform)
    ```
3.  **Reverse using API**: Use `path.reverse()` to flip direction while maintaining correct Bézier handle order and node types.
4.  **Manual Merge for Seams**: For symmetric mirroring where ends touch:
    *   Create a new `GSPath()`.
    *   Append Source nodes.
    *   Append **Reversed** Mirror nodes.
    *   Check for duplicates at the connection points (tolerance ~0.1 - 0.5 units).
    *   Set `closed = True`.
5.  **Replace In-Place**: To update a path, replace its `nodes` property rather than deleting/adding the path object itself.
    ```python
    original_path.nodes = [n.copy() for n in new_result.nodes]
    original_path.closed = new_result.closed
    ```

## 2. Glyphs API Quirks

*   **Script Execution**: Glyphs scripts don't run as `__main__` in the standard Python sense. Guarding code with `if __name__ == "__main__":` often prevents execution. Just call the main function.
*   **Menu Titles**: Scripts require a special comment header to appear in the menu:
    ```python
    #MenuTitle: My Script Name
    ```
*   **Node Selection**: You cannot set `.selected = True` on a `GSNode` that hasn't been added to a layer/path yet. Add it first, then select it.
*   **Proxy Objects**: `layer.paths` is a proxy object. It behaves like a list but has restrictions (e.g., some versions throw errors on `remove()`). Clearing nodes is a safer way to "empty" a path if removal fails.

## 3. Geometry Logic

*   **Seam Detection**: Relying solely on selected nodes to find a "seam" fails if the user selects a shape that doesn't touch the center.
*   **Bounds Fallback**: Always check if selected nodes actually lie on the mirror axis. If not, fall back to the **bounding box center** of the *entire* path to determine the axis.
    ```python
    axis = (min_coord + max_coord) / 2.0
    ```

## 4. Debugging

*   **Macro Panel**: `print()` output goes to the Macro Panel (Window > Macro Panel).
*   **Visual Debugging**: Print bounds, node counts, and key coordinates.
*   **Reloading**: Scripts are cached. Use **Script > Reload Scripts** after *every* file change. 
*   **Module Reloading**: If your script imports a local helper module (like `mirror_geometry`), you must force-reload it:
    ```python
    import importlib
    import mirror_geometry
    importlib.reload(mirror_geometry)
    ```

