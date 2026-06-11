"""Tag bulk-seed facts with venture metadata (ADR 003)."""

from __future__ import annotations

import copy
from pathlib import Path
from typing import Any

# ADR 003 venture vocabulary (must match scripts/memory.py VALID_VENTURES).
VALID_VENTURES = frozenset(
    {"trading_firm", "social_media", "ria", "personal", "career", "migration"}
)

# Path substring → venture (checked on normalized posix path).
_PATH_RULES: tuple[tuple[str, str], ...] = (
    ("trading-firm", "trading_firm"),
    ("trading_firm", "trading_firm"),
    ("/trading/", "trading_firm"),
    ("social-media", "social_media"),
    ("social_media", "social_media"),
    ("youtube", "social_media"),
    ("content-firm", "social_media"),
    ("/ria/", "ria"),
    ("ventures/ria", "ria"),
    ("career/", "career"),
    ("recruiter", "career"),
    ("migration/", "migration"),
    ("src/migration/", "migration"),
    ("docs/decisions/", "personal"),
    ("docs/design/", "personal"),
    ("docs/planning/", "personal"),
)

# Keyword groups → venture (checked on lowercased text).
_KEYWORD_RULES: tuple[tuple[tuple[str, ...], str], ...] = (
    (("iron condor", "nifty", "banknifty", "etf pledge", "algo trading"), "trading_firm"),
    (("youtube", "content firm", "social media"), "social_media"),
    (("registered investment adviser", "registered investment advisor", " ria "), "ria"),
    (("recruiter", "job search", "interview prep", "interview-prep"), "career"),
    (
        ("germany", "australia", "visa", "international migration", "phd deadline"),
        "migration",
    ),
)


def _normalize_path(source_path: str) -> str:
    return Path(source_path).as_posix().lower()


def _ventures_from_path(source_path: str) -> set[str]:
    normalized = _normalize_path(source_path)
    found: set[str] = set()
    for fragment, venture in _PATH_RULES:
        if fragment in normalized:
            found.add(venture)
    return found


def _ventures_from_text(text: str) -> set[str]:
    lowered = text.lower()
    found: set[str] = set()
    for keywords, venture in _KEYWORD_RULES:
        if any(keyword in lowered for keyword in keywords):
            found.add(venture)
    return found


def infer_ventures(*, source_path: str, text: str) -> list[str]:
    """Infer venture tags from document path and body text."""
    tags = _ventures_from_path(source_path) | _ventures_from_text(text)
    return sorted(v for v in tags if v in VALID_VENTURES)


def categorize_fact(fact: dict[str, Any]) -> dict[str, Any]:
    """Return a copy of *fact* with metadata.ventures set when inferable."""
    out = copy.deepcopy(fact)
    metadata = out.setdefault("metadata", {})
    existing = metadata.get("ventures")
    if isinstance(existing, list) and existing:
        metadata["ventures"] = sorted({str(v) for v in existing if v in VALID_VENTURES})
        return out

    source_path = str(metadata.get("source_doc_id") or "")
    text = str(out.get("text") or "")
    ventures = infer_ventures(source_path=source_path, text=text)
    if ventures:
        metadata["ventures"] = ventures
    else:
        metadata.pop("ventures", None)
    return out


def categorize_facts(facts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Apply :func:`categorize_fact` to each fact."""
    return [categorize_fact(fact) for fact in facts]
