# Mirror Script - Quick Start Guide

## 🚀 Get Started in 3 Steps

### 1. Activate the Script
In Glyphs 3, go to the menu:
```
Script > Reload Scripts
```

### 2. Select Your Half
**Two workflows:**

**A) Starting from scratch:**
- Draw one half + center seam nodes
- Select ALL nodes (Cmd+A)

**B) Updating existing shape:**
- Make changes to one half (left, right, top, or bottom)
- Select just the nodes on that half (including seam)
- The other half will be automatically replaced

### 3. Run the Script
```
Script > Mirror Selection
```
- Choose your source direction (Top/Right/Bottom/Left)
- Click "Mirror"
- Done! 🎉

## 📖 Example 1: Mirror Left to Right (New Shape)

```
Step 1: Draw left half of a circle
        • Include nodes on the center vertical line (x=0)

Step 2: Select everything (Cmd+A)

Step 3: Script > Mirror Selection
        • Choose "Left (mirror right)"
        • Click Mirror

Result: Full circle appears ✓
```

## 📖 Example 2: Update Existing Shape

```
Step 1: You have a full symmetric circle
        • Make changes to the left half

Step 2: Select ONLY the left half nodes (including center seam)

Step 3: Script > Mirror Selection
        • Choose "Left (mirror right)"
        • Click Mirror

Result: Right half is replaced with mirrored left ✓
```

## ⚙️ Settings

**"Snap seam nodes to axis first"** (checkbox)
- ✅ Checked (default): Auto-fixes slightly misaligned seam nodes
- ☐ Unchecked: Requires perfect alignment (will error if off)

💡 **Tip**: Keep it checked for easier workflow!

## 🎯 The 4 Directions

| Choose... | When you drew... | Result |
|-----------|------------------|--------|
| **Top** | Top half | Mirrors down |
| **Right** | Right half | Mirrors left |
| **Bottom** | Bottom half | Mirrors up |
| **Left** | Left half | Mirrors right |

## ⚠️ Common Mistakes

### ❌ "No seam points found"
**Problem**: You didn't select the center line nodes  
**Fix**: Make sure to select ALL nodes including those on the axis

### ❌ "Center points not aligned"
**Problem**: Your seam is crooked  
**Fix**: Enable "Snap seam nodes to axis first" or manually align

### ❌ "Seam validation failed"
**Problem**: Your selected seam nodes are not aligned  
**Fix**: Enable "Snap seam nodes to axis first" or manually align them

## 📚 More Info

- **Full documentation**: Read `Mirror_README.md`
- **Testing guide**: See `TESTING_GUIDE.md`
- **Implementation details**: Check `IMPLEMENTATION_SUMMARY.md`

## ✅ Verification

**Unit tests** (optional, for developers):
```bash
cd ~/Library/Application\ Support/Glyphs\ 3/Scripts
source venv/bin/activate
pytest test_mirror_geometry.py -v
```
Should show: **23 passed** ✅

## 🎨 Real-World Use Cases

Perfect for:
- Hearts, diamonds, arrows
- Symmetric letters (A, H, M, O, V, W, X, Y)
- Brackets, parentheses
- Ornaments and decorative elements
- Any symmetric icon or glyph

## 💡 Pro Tips

1. **Use guides**: Set up a guide at your seam axis for precise alignment
2. **Save often**: Use Cmd+S before mirroring (can undo with Cmd+Z)
3. **Keyboard shortcut**: Assign one via System Preferences for faster access
4. **Rough sketch**: Draw a rough other half first, it gets deleted automatically

## 🏁 That's It!

The script is ready to use. Enjoy symmetric design! 🎉

