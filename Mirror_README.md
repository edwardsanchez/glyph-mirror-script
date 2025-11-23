# Mirror Selection Script for Glyphs 3

A Glyphs script that mirrors selected glyph nodes across a seam axis (horizontal or vertical) with automatic seam snapping and strict validation.

## Features

- **4-way mirroring**: Mirror from Top, Right, Bottom, or Left
- **Automatic seam snapping**: Optional snapping of seam nodes to a shared axis
- **Strict validation**: Ensures all seam points are selected and aligned
- **Bézier handle support**: Correctly mirrors off-curve control points
- **Clean output**: Automatically removes overlaps and corrects path direction

## Installation

1. The script files should be in your Glyphs Scripts folder:
   ```
   ~/Library/Application Support/Glyphs 3/Scripts/
   ```

2. The following files should be present:
   - `Mirror.py` - Main script with UI
   - `mirror_geometry.py` - Core mirroring logic
   - `test_mirror_geometry.py` - Unit tests (optional)

3. In Glyphs, go to **Script > Reload Scripts** to make the script available

4. The script will appear in the **Script** menu as "Mirror Selection"

## Usage

### Two Workflows

#### Workflow A: Starting from Scratch

1. **Draw one half** of your symmetric shape (e.g., left half or top half)
2. **Include the seam nodes**: The seam is the center line where the two halves meet
3. **Select all nodes** on your half INCLUDING all seam nodes
4. **Run the script**: Script > Mirror Selection

#### Workflow B: Updating Existing Shape (Most Common!)

1. **Start with a full symmetric shape**
2. **Make changes to one half** (e.g., edit the left side)
3. **Select just that half** - select all nodes on the half you edited, including the center seam
4. **Run the script**: Script > Mirror Selection
5. **Result**: The opposite half is deleted and replaced with your mirrored changes

**Note**: The seam is the center line where the two halves meet:
- For left/right mirror: seam is a vertical line
- For top/bottom mirror: seam is a horizontal line

5. **Choose direction**:
   - **Top (mirror down)**: Use when you drew the top half
   - **Right (mirror left)**: Use when you drew the right half
   - **Bottom (mirror up)**: Use when you drew the bottom half
   - **Left (mirror right)**: Use when you drew the left half

6. **Optional**: Check "Snap seam nodes to axis first" to automatically align slightly misaligned seam nodes

7. **Click "Mirror"**

### Keyboard Shortcut (Optional)

You can assign a keyboard shortcut to the script:

1. Open **System Preferences > Keyboard > Shortcuts > App Shortcuts**
2. Click the **+** button
3. Choose **Glyphs** as the application
4. Enter the menu title exactly: `Mirror Selection`
5. Assign your preferred keyboard shortcut

## Requirements

### Seam Rules

The script validates your selection to ensure clean mirroring:

1. **Selected seam nodes must be aligned**
   - All **selected** seam on-curve nodes must share the same x-coordinate (for horizontal mirror)
   - Or share the same y-coordinate (for vertical mirror)
   - Default tolerance: 0.01 units
   - Use "Snap seam nodes to axis first" to auto-fix slight misalignment
   - Off-curve nodes (handles) don't need to be on the seam

2. **You don't need to select ALL seam nodes**
   - Just select the nodes on the half you're working with
   - Unselected nodes on the opposite half will be automatically deleted
   - This makes the "update existing shape" workflow easy

### What Gets Mirrored

- **Selected on-curve nodes**: Form the outline of your shape
- **Selected off-curve nodes**: Bézier handles that define curves
- **All nodes** on the selected half are duplicated and mirrored

### What Gets Deleted

- **Unselected nodes** on the opposite side of the seam are removed
- This allows you to have a rough sketch on the other side that gets replaced

## Examples

### Example 1: Left-to-Right Mirror

```
1. Draw left half of a circle
2. Select all left nodes + center vertical line nodes
3. Run script > Choose "Left (mirror right)"
4. Result: Full circle
```

### Example 2: Top-to-Bottom Mirror

```
1. Draw top half of a diamond
2. Select all top nodes + center horizontal line nodes
3. Run script > Choose "Top (mirror down)"
4. Result: Full diamond
```

## Troubleshooting

### "No nodes selected"
- Make sure you have selected at least some nodes before running the script

### "No seam points found"
- The script couldn't find any selected nodes near the calculated seam axis
- Make sure you selected the nodes on the center line (seam)
- The seam is detected as the furthest edge of your selection

### "Center points not aligned"
- Your seam nodes are not perfectly aligned on a straight line
- Either:
  - Manually align them in Glyphs (use guides)
  - Enable "Snap seam nodes to axis first" checkbox

### "Seam validation failed" / "Center points not aligned"
- Your **selected** seam nodes are not perfectly aligned on a straight line
- Either:
  - Manually align them in Glyphs (use guides)
  - Enable "Snap seam nodes to axis first" checkbox
- Note: You don't need to select seam nodes on the opposite half - they'll be deleted

## Technical Details

### Core Algorithm

1. Detect seam axis from selected nodes (min or max x/y)
2. Validate all seam on-curve nodes are aligned
3. Optionally snap seam nodes to average position
4. Delete unselected nodes on opposite side
5. Duplicate and mirror selected paths using `applyTransform()`
6. Merge paths with `removeOverlap()` and `correctPathDirection()`

### Transform Matrices

- **Horizontal mirror** around x=a: `(-1, 0, 0, 1, 2a, 0)`
- **Vertical mirror** around y=b: `(1, 0, 0, -1, 0, 2b)`

### Parameters

- `center_band = 5.0` - Distance from seam axis to consider a node "on the seam"
- `eps = 0.01` - Tolerance for alignment checks

## Unit Tests

The `mirror_geometry.py` module has comprehensive unit tests in `test_mirror_geometry.py`.

To run tests:

```bash
cd ~/Library/Application\ Support/Glyphs\ 3/Scripts
python3 -m venv venv
source venv/bin/activate
pip install pytest
pytest test_mirror_geometry.py -v
```

All 23 tests should pass.

## Files

- **Mirror.py**: Main script with Vanilla UI dialog and Glyphs integration
- **mirror_geometry.py**: Pure Python geometry logic (no Glyphs dependencies)
- **test_mirror_geometry.py**: Unit tests for mirror_geometry module
- **requirements.txt**: Python dependencies for testing
- **Mirror_README.md**: This file

## Author

Created for Glyphs 3 based on conversation about simplifying symmetric glyph design workflows.

## License

Use freely for your font design projects.

