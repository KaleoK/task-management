#!/usr/bin/env python3
"""
Archive completed one-time tasks from tasks/tasks.md to completed/completed.md.
Recurring tasks (those with (recurs: ...) marker) have their due date advanced instead.
"""

import re
from datetime import datetime, timedelta
from pathlib import Path

from config import get_tasks_root, get_folder


def advance_due_date(due_str, recurrence):
    """Return next due date string based on recurrence type."""
    current = datetime.strptime(due_str, '%Y-%m-%d')
    r = recurrence.strip().lower()
    if r == 'daily':
        next_due = current + timedelta(days=1)
    elif r == 'monthly':
        month = current.month + 1
        year = current.year + (month - 1) // 12
        month = ((month - 1) % 12) + 1
        next_due = current.replace(year=year, month=month)
    elif r == 'weekly':
        next_due = current + timedelta(weeks=1)
    elif r == 'biweekly':
        next_due = current + timedelta(weeks=2)
    elif r == 'quarterly':
        month = current.month + 3
        year = current.year + (month - 1) // 12
        month = ((month - 1) % 12) + 1
        next_due = current.replace(year=year, month=month)
    elif r == 'yearly':
        next_due = current.replace(year=current.year + 1)
    else:
        return due_str
    return next_due.strftime('%Y-%m-%d')


def archive_completed_tasks():
    tasks_file = get_tasks_root() / "Tasks.md"
    completed_file = get_tasks_root() / "Completed.md"
    today = datetime.today().strftime('%Y-%m-%d')

    if not tasks_file.exists():
        print("No tasks file found.")
        return

    lines = tasks_file.read_text(encoding='utf-8').splitlines(keepends=True)
    new_lines = []
    archived = []
    updated_recurring = []

    for line in lines:
        m = re.match(r'^- \[x\] (.+)\n?$', line)
        if not m:
            new_lines.append(line)
            continue

        content = m.group(1)
        due_m = re.search(r'\(due: (\d{4}-\d{2}-\d{2})\)', content)
        recurs_m = re.search(r'\(recurs: ([^)]+)\)', content)
        name = re.sub(r'\s*\([^)]+\)', '', content).strip()

        if recurs_m:
            # Advance due date and reset to incomplete
            old_due = due_m.group(1) if due_m else None
            new_due = advance_due_date(old_due, recurs_m.group(1)) if old_due else old_due
            new_content = content.replace(f"(due: {old_due})", f"(due: {new_due})")
            new_lines.append(f"- [ ] {new_content}\n")
            updated_recurring.append(f"{name} → next due: {new_due}")
        else:
            # Archive to completed.md
            due_info = f" (due: {due_m.group(1)})" if due_m else ""
            archived.append(f"- [x] {name}{due_info} (completed: {today})\n")

    tasks_file.write_text(''.join(new_lines), encoding='utf-8')

    if archived:
        if not completed_file.exists():
            completed_file.write_text("", encoding='utf-8')
        with open(completed_file, 'a', encoding='utf-8') as f:
            for entry in archived:
                f.write(entry)

    if archived:
        print(f"Archived {len(archived)} completed task(s):")
        for entry in archived:
            print(f"  - {entry.strip()}")
    if updated_recurring:
        print(f"Updated {len(updated_recurring)} recurring task(s):")
        for entry in updated_recurring:
            print(f"  - {entry}")
    if not archived and not updated_recurring:
        print("No completed tasks to archive.")


def main():
    print("=== Archiving Completed Tasks ===\n")
    archive_completed_tasks()


if __name__ == "__main__":
    main()
