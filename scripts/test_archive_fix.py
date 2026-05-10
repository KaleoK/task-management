import importlib.util
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))


def _load_archive():
    spec = importlib.util.spec_from_file_location(
        "archive_tasks",
        Path(__file__).parent / "archive-tasks.py"
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _make_view(tmp_dir, filename, content):
    p = Path(tmp_dir) / filename
    p.write_text(content, encoding='utf-8')


def test_archive_picks_up_checked_in_view_file(monkeypatch, tmp_path):
    """Tasks checked [x] in Today.md are archived even if Tasks.md still has [ ]."""
    arc = _load_archive()
    (tmp_path / "Tasks.md").write_text(
        "- [ ] Buy milk (due: 2026-05-09) (p:med) (cat:personal)\n", encoding='utf-8'
    )
    _make_view(tmp_path, "Today.md", "- [x] Buy milk\n")
    monkeypatch.setattr(arc, 'get_tasks_root', lambda: tmp_path)

    arc.archive_completed_tasks()

    remaining = (tmp_path / "Tasks.md").read_text(encoding='utf-8')
    completed = (tmp_path / "Completed.md").read_text(encoding='utf-8')
    assert "Buy milk" not in remaining
    assert "Buy milk" in completed
    assert "(completed:" in completed


def test_archive_handles_uppercase_X(monkeypatch, tmp_path):
    """Tasks checked [X] (uppercase) in Tasks.md are archived."""
    arc = _load_archive()
    (tmp_path / "Tasks.md").write_text(
        "- [X] Pay rent (due: 2026-05-28) (p:low) (cat:finance)\n", encoding='utf-8'
    )
    monkeypatch.setattr(arc, 'get_tasks_root', lambda: tmp_path)

    arc.archive_completed_tasks()

    remaining = (tmp_path / "Tasks.md").read_text(encoding='utf-8')
    completed = (tmp_path / "Completed.md").read_text(encoding='utf-8')
    assert "Pay rent" not in remaining
    assert "Pay rent" in completed


def test_archive_view_checked_recurring_advances_date(monkeypatch, tmp_path):
    """Recurring tasks checked in a view file advance their due date instead of archiving."""
    arc = _load_archive()
    (tmp_path / "Tasks.md").write_text(
        "- [ ] Tidy Up (due: 2026-05-09) (p:med) (recurs: daily) (cat:personal)\n", encoding='utf-8'
    )
    _make_view(tmp_path, "Today.md", "- [x] Tidy Up\n")
    monkeypatch.setattr(arc, 'get_tasks_root', lambda: tmp_path)

    arc.archive_completed_tasks()

    remaining = (tmp_path / "Tasks.md").read_text(encoding='utf-8')
    assert "- [ ] Tidy Up" in remaining
    assert "2026-05-10" in remaining
    assert not (tmp_path / "Completed.md").exists()


def test_archive_unchecked_task_not_archived(monkeypatch, tmp_path):
    """Tasks unchecked in both Tasks.md and view files are left alone."""
    arc = _load_archive()
    (tmp_path / "Tasks.md").write_text(
        "- [ ] Cook (due: 2026-05-09) (p:med) (cat:personal)\n", encoding='utf-8'
    )
    _make_view(tmp_path, "Today.md", "- [ ] Cook\n")
    monkeypatch.setattr(arc, 'get_tasks_root', lambda: tmp_path)

    arc.archive_completed_tasks()

    remaining = (tmp_path / "Tasks.md").read_text(encoding='utf-8')
    assert "Cook" in remaining
    assert not (tmp_path / "Completed.md").exists()
