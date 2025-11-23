# Git Guide for Mirror Script

This repository tracks changes to the Mirror script for Glyphs 3.

## Quick Reference

### Check Status
```bash
cd ~/Library/Application\ Support/Glyphs\ 3/Scripts
git status
```

### View Changes
```bash
git diff                    # View unstaged changes
git diff --staged          # View staged changes
git log --oneline          # View commit history
git log --oneline -10      # Last 10 commits
```

### Make Changes and Commit
```bash
# After editing files
git add Mirror.py                    # Stage specific file
git add .                            # Stage all changes
git commit -m "Description of changes"
```

### View History
```bash
git log                              # Full history
git log --oneline --graph            # Visual graph
git show                             # Show last commit details
git show <commit-hash>               # Show specific commit
```

### Undo Changes
```bash
# Discard uncommitted changes
git checkout -- Mirror.py            # Discard changes to specific file
git reset --hard                     # Discard ALL uncommitted changes (careful!)

# Undo last commit (keep changes)
git reset --soft HEAD~1

# Undo last commit (discard changes)
git reset --hard HEAD~1             # CAREFUL! This deletes work
```

### Compare Versions
```bash
git diff HEAD~1 Mirror.py           # Compare with previous version
git diff <commit1> <commit2>        # Compare two commits
```

### Branches (Optional)
```bash
git branch                          # List branches
git branch experimental             # Create new branch
git checkout experimental           # Switch to branch
git checkout -b new-feature         # Create and switch
git merge experimental              # Merge branch into current
```

## Common Workflows

### After Making Changes
```bash
cd ~/Library/Application\ Support/Glyphs\ 3/Scripts

# 1. Check what changed
git status
git diff

# 2. Stage your changes
git add Mirror.py mirror_geometry.py

# 3. Commit with a message
git commit -m "Fix: Handle edge case when seam has no nodes"

# 4. Verify
git log --oneline -3
```

### Experimenting Safely
```bash
# Create experimental branch
git checkout -b try-new-algorithm

# Make changes and test
# ... edit files ...

# If it works, merge back
git checkout master
git merge try-new-algorithm

# If it doesn't work, just switch back
git checkout master
# The experimental branch remains for later
```

### Roll Back to Previous Version
```bash
# Find the commit you want
git log --oneline

# Create a new branch at that point (safe)
git checkout -b revert-to-working <commit-hash>

# Or overwrite current state (careful!)
git reset --hard <commit-hash>
```

## Files Tracked

Currently tracking:
- `Mirror.py` - Main script
- `mirror_geometry.py` - Core logic
- `test_mirror_geometry.py` - Unit tests
- `requirements.txt` - Dependencies
- `QUICKSTART.md` - Quick start guide
- `Mirror_README.md` - Full documentation
- `TESTING_GUIDE.md` - Manual testing
- `IMPLEMENTATION_SUMMARY.md` - Technical overview
- `UPDATE_v1.1.md` - Version changelog

## Files Ignored (.gitignore)

Not tracked:
- `venv/` - Virtual environment
- `__pycache__/` - Python cache
- `.pytest_cache/` - Test cache
- `fontTools`, `robofab`, `vanilla` - Symlinks to other repos
- `.DS_Store` - macOS metadata

## Current State

```
Repository: /Users/edwardsanchez/Library/Application Support/Glyphs 3/Scripts/.git
Branch: master
Initial commit: f36ff80 - Mirror script v1.1
```

## Tips

### Write Good Commit Messages
```
✅ Good:
"Fix: Seam validation now allows unselected opposite-side nodes"
"Add: Support for updating existing symmetric shapes"
"Docs: Clarify two-workflow approach in QUICKSTART"

❌ Bad:
"fix"
"updates"
"changes"
```

### Commit Often
- Commit after each logical change
- Don't wait until you have many unrelated changes
- Small commits are easier to understand and revert

### Before Committing
```bash
# Always check what you're committing
git status
git diff
```

### Create Tags for Versions
```bash
git tag v1.1 -m "Version 1.1 - Support update workflow"
git tag v1.2 -m "Version 1.2 - Add keyboard shortcuts"
git tag                     # List all tags
```

## Backup Strategy

This git repository is **local only** (no remote). Consider:

1. **Manual backup**: Copy `.git` folder periodically
2. **Remote repository**: Push to GitHub/GitLab
3. **Time Machine**: macOS backup includes git repo

### Push to GitHub (Optional)
```bash
# Create empty repo on GitHub first, then:
git remote add origin https://github.com/yourusername/glyphs-mirror-script.git
git push -u origin master
```

## Help

```bash
git help                    # General help
git help commit             # Help for specific command
git <command> --help        # Same as above
```

## Quick Recovery

If you mess up:
```bash
# See what you did
git reflog

# Go back to before you messed up
git reset --hard HEAD@{1}
```

---

**Repository initialized**: November 23, 2025  
**Current version**: v1.1  
**Total commits**: Check with `git log --oneline | wc -l`

