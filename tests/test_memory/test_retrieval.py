from __future__ import annotations

from memory.retrieval import latest_by_event_date, record_text


def test_latest_by_event_date_ignores_write_order() -> None:
    records = [
        {
            "memory": "cancelled",
            "metadata": {"event_date": "2026-05-15"},
            "created_at": "2026-06-11T12:00:00Z",
        },
        {
            "memory": "implementation started",
            "metadata": {"event_date": "2026-06-10"},
            "created_at": "2026-06-10T08:00:00Z",
        },
        {
            "memory": "planning",
            "metadata": {"event_date": "2026-06-01"},
        },
    ]
    latest = latest_by_event_date(records)
    assert latest is not None
    assert record_text(latest) == "implementation started"
