#!/usr/bin/env python3
"""
Generate Today.md, This Week.md, and Next Week.md files.

Reads tasks from tasks/tasks.md and ideas from ideas/ideas.md
using checklist format:  - [ ] Task name (due: YYYY-MM-DD)
"""

import re
import sys
from datetime import datetime, timedelta
from pathlib import Path

from config import get_tasks_root, get_folder
from dates import get_week_dates

BASE_DIR = get_tasks_root()
TASKS_FILE = BASE_DIR / "Tasks.md"
IDEAS_FILE = BASE_DIR / "Undated.md"
SCRIPTS_DIR = Path(__file__).parent

PRIORITY_ORDER = {'high': 0, 'med': 1, 'low': 2, None: 3}
PRIORITY_SPANS = {
    'high': '<span class="p-high">!</span>',
    'med':  '<span class="p-med">!</span>',
    'low':  '<span class="p-low">!</span>',
}


def normalize_dates():
    """Run the normalize-dates.py script."""
    print("Normalizing dates...")
    import subprocess
    result = subprocess.run(
        f"python3 {SCRIPTS_DIR}/normalize-dates.py",
        shell=True, cwd=BASE_DIR, capture_output=True, text=True
    )
    print(result.stdout.strip())
    if result.stderr:
        print(f"Error: {result.stderr.strip()}", file=sys.stderr)


def archive_completed_tasks():
    """Run the archive-tasks.py script."""
    print("\nArchiving completed tasks...")
    import subprocess
    result = subprocess.run(
        f"python3 {SCRIPTS_DIR}/archive-tasks.py",
        shell=True, cwd=BASE_DIR, capture_output=True, text=True
    )
    if result.stdout:
        for line in result.stdout.strip().split('\n'):
            if not line.startswith("==="):
                print(line)
    if result.stderr:
        print(f"Error: {result.stderr.strip()}", file=sys.stderr)


def parse_tasks():
    """Parse tasks/tasks.md and return list of task dicts."""
    if not TASKS_FILE.exists():
        return []
    tasks = []
    with open(TASKS_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.rstrip()
            m = re.match(r'^- \[([ x])\] (.+)$', line)
            if not m:
                continue
            is_complete = m.group(1) == 'x'
            content = m.group(2)
            due_m = re.search(r'\(due: (\d{4}-\d{2}-\d{2})\)', content)
            due_date = due_m.group(1) if due_m else None
            p_m = re.search(r'\(p:(high|med|low)\)', content)
            priority = p_m.group(1) if p_m else None
            name = re.sub(r'\s*\([^)]+\)', '', content).strip()
            tasks.append({'name': name, 'due': due_date, 'complete': is_complete, 'priority': priority})
    return tasks


def get_tasks_for_date(date):
    """Get tasks due on a specific date, sorted by priority."""
    tasks = [t for t in parse_tasks() if t['due'] == date and not t['complete']]
    return sorted(tasks, key=lambda t: PRIORITY_ORDER.get(t['priority'], 3))


def get_overdue_tasks(today):
    """Get overdue tasks sorted by priority."""
    today_date = datetime.strptime(today, '%Y-%m-%d')
    result = []
    for t in parse_tasks():
        if t['due'] and not t['complete']:
            try:
                if datetime.strptime(t['due'], '%Y-%m-%d') < today_date:
                    result.append(t)
            except ValueError:
                pass
    return sorted(result, key=lambda t: PRIORITY_ORDER.get(t['priority'], 3))


def get_in_progress_ideas():
    """Get ideas listed under ## In Progress in ideas/ideas.md."""
    if not IDEAS_FILE.exists():
        return []
    ideas = []
    in_section = False
    with open(IDEAS_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.rstrip()
            if re.match(r'^## In Progress', line, re.IGNORECASE):
                in_section = True
                continue
            if re.match(r'^## ', line) and in_section:
                break
            if in_section and line.startswith('- '):
                idea = line[2:].strip()
                if idea:
                    ideas.append(idea)
    return ideas


def generate_days_between(start_date, end_date):
    """Generate list of dates between start and end (inclusive)."""
    start = datetime.strptime(start_date, '%Y-%m-%d')
    end = datetime.strptime(end_date, '%Y-%m-%d')
    days = []
    current = start
    while current <= end:
        days.append(current)
        current += timedelta(days=1)
    return days


def format_date_header(date):
    """Format date as 'Monday, October 7'."""
    return date.strftime('%A, %B %-d')


def render_tasks(tasks):
    """Render tasks grouped by priority with blank lines between groups, colored ! prefix."""
    from itertools import groupby
    lines = []
    for _, group in groupby(tasks, key=lambda t: t['priority']):
        for t in group:
            span = PRIORITY_SPANS.get(t['priority'], '')
            prefix = f"{span} " if span else ""
            lines.append(f"- [ ] {prefix}{t['name']}")
        lines.append("")
    while lines and lines[-1] == "":
        lines.pop()
    return "\n".join(lines) + "\n" if lines else ""


def generate_today_md(dates):
    """Generate Today.md file."""
    print("\nGenerating Today.md...")
    today = dates['today']
    today_dt = datetime.strptime(today, '%Y-%m-%d')

    overdue = get_overdue_tasks(today)
    due_today = get_tasks_for_date(today)
    ideas = get_in_progress_ideas()

    content = f"#### {format_date_header(today_dt)}\n\n"

    if due_today:
        content += render_tasks(due_today)
        content += "\n"

    if ideas:
        content += "## In Progress Ideas\n"
        for idea in ideas:
            content += f"- {idea}\n"
        content += "\n"

    if overdue:
        content += "#### Overdue\n\n"
        content += render_tasks([{**t, 'name': f"{t['name']} (due: {t['due']})"} for t in overdue])
        content += "\n"

    with open(BASE_DIR / "Today.md", 'w') as f:
        f.write(content)

    print(f"  - {len(overdue)} overdue task(s)")
    print(f"  - {len(due_today)} task(s) due today")
    print(f"  - {len(ideas)} in-progress idea(s)")


def generate_this_week_md(dates):
    """Generate This Week.md file."""
    print("\nGenerating This Week.md...")
    tomorrow = dates['tomorrow']
    week_end = dates['this_week_end']
    tomorrow_dt = datetime.strptime(tomorrow, '%Y-%m-%d')
    week_end_dt = datetime.strptime(week_end, '%Y-%m-%d')

    content = ""

    if tomorrow_dt > week_end_dt:
        content += "No tasks remaining this week.\n"
        with open(BASE_DIR / "This Week.md", 'w') as f:
            f.write(content)
        print("  - No days remaining this week")
        return

    days = generate_days_between(tomorrow, week_end)
    total_tasks = 0
    for day in days:
        tasks = get_tasks_for_date(day.strftime('%Y-%m-%d'))
        if tasks:
            content += f"#### {day.strftime('%B %-d')}\n\n"
            content += render_tasks(tasks)
            content += "\n"
            total_tasks += len(tasks)

    with open(BASE_DIR / "This Week.md", 'w') as f:
        f.write(content)
    print(f"  - {total_tasks} task(s) across {len(days)} day(s)")


def generate_next_week_md(dates):
    """Generate Next Week.md file."""
    print("\nGenerating Next Week.md...")
    week_start = dates['next_week_start']
    week_end = dates['next_week_end']
    week_start_dt = datetime.strptime(week_start, '%Y-%m-%d')

    content = ""
    days = generate_days_between(week_start, week_end)
    total_tasks = 0
    for day in days:
        tasks = get_tasks_for_date(day.strftime('%Y-%m-%d'))
        if tasks:
            content += f"#### {format_date_header(day)}\n\n"
            content += render_tasks(tasks)
            content += "\n"
            total_tasks += len(tasks)

    with open(BASE_DIR / "Next Week.md", 'w') as f:
        f.write(content)
    print(f"  - {total_tasks} task(s) across {len(days)} day(s)")


def main():
    print("=== Generating Daily Task Files ===\n")
    normalize_dates()
    dates = get_week_dates()
    print(f"Calculating week dates...")
    print(f"Today: {dates['today_weekday']}, {dates['today_formatted']} ({dates['today']})")
    print(f"This week: {dates['this_week_start']} to {dates['this_week_end']}")
    print(f"Next week: {dates['next_week_start']} to {dates['next_week_end']}")
    archive_completed_tasks()
    generate_today_md(dates)
    generate_this_week_md(dates)
    generate_next_week_md(dates)
    print("\n=== Done! ===")


if __name__ == "__main__":
    main()
