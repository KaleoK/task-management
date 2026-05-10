---
description: Generate Today.md, This Week.md, and Next Week.md
---

# today

Generate Today.md, This Week.md, and Next Week.md.

## Process

Run:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/generate-daily-files.py
```

This script:
1. Normalizes dates in Tasks.md
2. Archives completed tasks to Completed.md (advances due date for recurring tasks)
3. Generates all three view files

## Example Output — Today.md

```markdown
#### Saturday, May 9

**Admin**
- [ ] <span class="p-high">!</span> Complete CM's form
- [ ] <span class="p-high">!</span> Find Binder

**Personal**
- [ ] <span class="p-med">!</span> Cook
- [ ] <span class="p-med">!</span> Tidy Up
```

## Example Output — This Week.md

```markdown
#### Week Notes

#### Sunday, May 10

**Finance**
- [ ] <span class="p-high">!</span> Review Investments

**Personal**
- [ ] <span class="p-med">!</span> Do Laundry
```
