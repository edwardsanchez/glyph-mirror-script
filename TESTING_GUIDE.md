# Manual Testing Guide for Mirror Script

This guide provides step-by-step instructions for manually testing the Mirror script in Glyphs 3.

## Prerequisites

1. Glyphs 3 is installed and running
2. All script files are in place:
   - `Mirror.py`
   - `mirror_geometry.py`
   - `test_mirror_geometry.py`
3. You've run **Script > Reload Scripts** in Glyphs

## Automated Tests (Run First)

Before manual testing, verify the unit tests pass:

```bash
cd ~/Library/Application\ Support/Glyphs\ 3/Scripts
source venv/bin/activate
pytest test_mirror_geometry.py -v
```

**Expected result**: All 23 tests pass.

---

## Manual Test Cases

### Test 1: Simple Left-to-Right Mirror (Basic Functionality)

**Goal**: Verify basic horizontal mirroring works

**Steps**:
1. Create a new glyph or open an existing one
2. Draw a simple left half:
   - Use the Pen tool
   - Draw points: `(-100, 0)`, `(-50, 100)`, `(0, 100)`, `(0, 0)`
   - Make it a closed path
3. Select ALL nodes (Cmd+A or manually select all 4 points)
4. Run **Script > Mirror Selection**
5. Choose "Left (mirror right)"
6. Check "Snap seam nodes to axis first" (should be checked by default)
7. Click **Mirror**

**Expected result**:
- The shape is now symmetric
- You see both left and right halves
- The seam at x=0 has no duplicated points
- No error dialogs appear

**Visual check**: The shape should look like a symmetric diamond or tent

---

### Test 2: Top-to-Bottom Mirror (Vertical Axis)

**Goal**: Verify vertical mirroring works

**Steps**:
1. Create a new glyph
2. Draw a simple top half:
   - Points: `(0, 200)`, `(100, 200)`, `(50, 250)`
   - Closed path
3. Select all nodes
4. Run **Script > Mirror Selection**
5. Choose "Top (mirror down)"
6. Click **Mirror**

**Expected result**:
- The shape is mirrored downward
- Seam is at y=200
- Symmetric shape appears

---

### Test 3: Curves with Bézier Handles

**Goal**: Verify off-curve control points mirror correctly

**Steps**:
1. Create a new glyph
2. Draw a curved left half:
   - Start with the Pen tool
   - Add a point at `(-100, 0)`
   - Add a curve point at `(0, 100)` with handles extending left
   - Add a point at `(0, 0)`
   - Close the path
3. Select ALL nodes (including handles)
4. Run **Script > Mirror Selection**
5. Choose "Left (mirror right)"
6. Click **Mirror**

**Expected result**:
- The curve is mirrored smoothly
- No kinks or breaks at the seam
- Handles on the right side point in mirrored directions

**Visual check**: Zoom in on the seam - the curve should be smooth with no visible discontinuity

---

### Test 4: Seam Alignment Error (Expected Failure)

**Goal**: Verify the script catches misaligned seam nodes

**Steps**:
1. Create a new glyph
2. Draw a left half with intentionally misaligned seam:
   - Point at `(-100, 0)`
   - Point at `(0, 50)`
   - Point at `(2, 100)` ← intentionally at x=2 instead of x=0
   - Point at `(0, 0)`
3. Uncheck "Snap seam nodes to axis first"
4. Select all nodes
5. Run **Script > Mirror Selection**
6. Choose "Left (mirror right)"
7. Click **Mirror**

**Expected result**:
- Error dialog appears: "Seam validation failed"
- Message mentions points not aligned
- No mirroring occurs
- Original shape remains unchanged

**Now test the fix**:
8. Close the error dialog
9. Re-run the script
10. This time, CHECK "Snap seam nodes to axis first"
11. Click **Mirror**

**Expected result**:
- No error
- Mirroring succeeds
- The misaligned point was automatically snapped to x=0

---

### Test 5: Unselected Seam Node (Expected Failure)

**Goal**: Verify the script catches when not all seam nodes are selected

**Steps**:
1. Create a new glyph
2. Draw a simple shape with multiple seam nodes:
   - Point at `(-100, 0)`
   - Point at `(0, 50)` ← seam node
   - Point at `(0, 100)` ← seam node
   - Point at `(0, 0)` ← seam node
3. Select only SOME nodes:
   - Select the left point: `(-100, 0)`
   - Select only two of the three seam nodes (skip one)
4. Run **Script > Mirror Selection**
5. Choose "Left (mirror right)"
6. Click **Mirror**

**Expected result**:
- Error dialog: "Unselected seam point"
- Message says all on-curve nodes on seam must be selected
- No mirroring occurs

**Fix and retry**:
7. Close the error
8. Select ALL nodes (Cmd+A)
9. Re-run the script and click **Mirror**

**Expected result**: Mirroring succeeds

---

### Test 6: Right-Side Source

**Goal**: Verify mirroring from right to left works

**Steps**:
1. Create a new glyph
2. Draw a RIGHT half:
   - Points: `(0, 0)`, `(0, 100)`, `(100, 50)`
   - Closed path
3. Select all nodes
4. Run **Script > Mirror Selection**
5. Choose "Right (mirror left)"
6. Click **Mirror**

**Expected result**:
- Shape is mirrored to the left
- Full symmetric shape appears
- Seam is at x=0

---

### Test 7: Bottom-Side Source

**Goal**: Verify mirroring from bottom to top

**Steps**:
1. Create a new glyph
2. Draw a BOTTOM half:
   - Points: `(0, 0)`, `(100, 0)`, `(50, -100)`
   - Closed path
3. Select all nodes
4. Run **Script > Mirror Selection**
5. Choose "Bottom (mirror up)"
6. Click **Mirror**

**Expected result**:
- Shape is mirrored upward
- Seam is at y=0
- Symmetric shape

---

### Test 8: Complex Shape (Real-World Scenario)

**Goal**: Test with a realistic glyph like a heart or arrow

**Steps**:
1. Create a new glyph
2. Draw the left half of a heart shape:
   - Include the curved top
   - Straight diagonal down to the center point at bottom
   - Multiple curve points with handles
3. Ensure the seam (vertical center line) has several on-curve nodes
4. Select ALL nodes
5. Run **Script > Mirror Selection**
6. Choose "Left (mirror right)"
7. Click **Mirror**

**Expected result**:
- Full heart shape appears
- Curves are smooth on both sides
- No visible artifacts at the seam
- `removeOverlap()` has cleaned up any overlapping paths

**Quality checks**:
- Zoom in to 800% on the seam
- Check for smooth curves
- Verify no duplicate points
- Check that path direction is correct (should be counter-clockwise for outer contours)

---

### Test 9: Multiple Paths

**Goal**: Verify script works with multiple separate paths (e.g., compound glyph)

**Steps**:
1. Create a new glyph
2. Draw TWO separate left halves:
   - First shape: small circle on the left at `(-80, 100)`
   - Second shape: larger outline below it
   - Make sure both have seam nodes at x=0
3. Select ALL nodes in BOTH paths
4. Run **Script > Mirror Selection**
5. Choose "Left (mirror right)"
6. Click **Mirror**

**Expected result**:
- Both shapes are mirrored
- You see symmetric compound shape
- Both paths were handled correctly

---

### Test 10: No Selection (Expected Failure)

**Goal**: Verify script handles the case when nothing is selected

**Steps**:
1. Open any glyph
2. Deselect all nodes (click empty space)
3. Run **Script > Mirror Selection**

**Expected result**:
- Dialog appears immediately: "No nodes selected"
- Suggests selecting nodes and trying again
- Script does not show the main UI window

---

## Performance Test (Optional)

**Goal**: Verify the script works with complex glyphs

**Steps**:
1. Create or open a very complex glyph (100+ nodes)
2. Draw only the left half with many curve points
3. Select all
4. Run the mirror script
5. Time how long it takes

**Expected result**:
- Should complete in < 2 seconds
- No lag or freezing
- Result is accurate

---

## Regression Checklist

After each test, verify:

- [ ] No duplicate points at seam
- [ ] Smooth curves (no kinks)
- [ ] Correct path direction (check with **Filter > Correct Path Direction** - should show no changes)
- [ ] No overlapping paths (run **Filter > Remove Overlap** - should show "already correct")
- [ ] Original selection is preserved or deselected appropriately
- [ ] Undo works (Cmd+Z should revert to pre-mirror state)

---

## Summary

If all tests pass:
- ✅ Basic horizontal and vertical mirroring works
- ✅ Error handling is robust
- ✅ Seam validation catches common mistakes
- ✅ Auto-snapping fixes small alignment issues
- ✅ Bézier curves are handled correctly
- ✅ Multiple paths work
- ✅ All edge cases are covered

The script is ready for production use!

---

## Reporting Issues

If any test fails:
1. Note which test failed
2. Take a screenshot of the error dialog (if any)
3. Note the exact steps that caused the failure
4. Check the Macro Panel (Window > Macro Panel) for any Python errors
5. Include glyph coordinates if relevant

Common issues:
- **Import errors**: Make sure `mirror_geometry.py` is in the same folder as `Mirror.py`
- **Vanilla UI not appearing**: Check that Glyphs has the vanilla module installed
- **Transform not working**: Verify Glyphs version is 3.x

