"""Test priority derivation and sort order."""
import sys
from pathlib import Path

# Allow running from any cwd
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from packets.serial_schema import priority_from_category, Category


def test_category_mapping():
    assert priority_from_category(int(Category.TRAPPED)) == 1, "TRAPPED must be CRITICAL (1)"
    assert priority_from_category(int(Category.FIRE)) == 1, "FIRE must be CRITICAL (1)"
    assert priority_from_category(int(Category.MEDICAL)) == 2, "MEDICAL must be HIGH (2)"
    assert priority_from_category(int(Category.OTHER)) == 3, "OTHER must be MEDIUM (3)"
    assert priority_from_category(int(Category.FLOOD)) == 3, "FLOOD must be MEDIUM (3)"
    assert priority_from_category(int(Category.UNKNOWN)) == 3, "UNKNOWN must be MEDIUM (3)"
    assert priority_from_category(0) == 3, "raw 0 must be MEDIUM (3)"
    print("  category_mapping: PASSED")


def test_priority_sort_order():
    reports = [
        {"id": 1, "priority": 3, "created_at": "2026-01-01T00:00:00"},
        {"id": 2, "priority": 1, "created_at": "2026-01-01T00:01:00"},
        {"id": 3, "priority": 2, "created_at": "2026-01-01T00:02:00"},
        {"id": 4, "priority": 1, "created_at": "2026-01-01T00:03:00"},
    ]
    sorted_reports = sorted(reports, key=lambda r: (r["priority"], r["created_at"]))
    ids = [r["id"] for r in sorted_reports]
    assert ids[0] == 2, f"Expected id=2 first (P1 earliest), got {ids}"
    assert ids[1] == 4, f"Expected id=4 second (P1 later), got {ids}"
    assert ids[2] == 3, f"Expected id=3 third (P2), got {ids}"
    assert ids[3] == 1, f"Expected id=1 last (P3), got {ids}"
    print("  priority_sort_order: PASSED")


if __name__ == "__main__":
    print("Running priority tests...")
    test_category_mapping()
    test_priority_sort_order()
    print("All tests PASSED.")
