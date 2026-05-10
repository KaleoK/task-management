#!/usr/bin/env python3
"""
Normalize date formats in tasks/tasks.md checklist to YYYY-MM-DD.

Handles:
- M/D/YYYY or MM/DD/YYYY  (e.g., 5/12/2026)
- YYYY-M-D                (e.g., 2026-5-9)
- YYYY-MM-DD              (already correct)
"""

import re
from pathlib import Path
from datetime import datetime

from config import get_tasks_root


def parse_date(date_str):
    date_str = date_str.strip()
    if '/' in date_str:
        for fmt in ('%m/%d/%Y', '%m/%d/%y'):
            try:
                return datetime.strptime(date_str, fmt).strftime('%Y-%m-%d')
            except ValueError:
                pass
    if '-' in date_str:
        parts = date_str.split('-')
        if len(parts) == 3:
            year, month, day = parts
            return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
    return date_str


def normalize_file(file_path):
    """Normalize (due: ...) dates in a checklist file. Returns True if modified."""
    if not file_path.exists():
        return False

    content = file_path.read_text(encoding='utf-8')
    modified = False

    def replace_due(m):
        nonlocal modified
        normalized = parse_date(m.group(1))
        if normalized != m.group(1):
            modified = True
            return f'(due: {normalized})'
        return m.group(0)

    new_content = re.sub(r'\(due: ([^)]+)\)', replace_due, content)

    if modified:
        file_path.write_text(new_content, encoding='utf-8')
    return modified


def main():
    modified = []
    root = get_tasks_root()
    for fname in ("Tasks.md", "Ideas.md"):
        f = root / fname
        if normalize_file(f):
            modified.append(str(f))

    if modified:
        print(f"Normalized dates in {len(modified)} file(s):")
        for f in modified:
            print(f"  - {f}")
    else:
        print("No files needed date normalization.")


if __name__ == '__main__':
    main()
