"""Unit tests for markdown → bulk-seed fact parsing (Phase 5)."""

from __future__ import annotations

import datetime as _dt
from pathlib import Path

from migration import import_md

SAMPLE = """\
Preamble paragraph before any heading.

# Top level

Intro under top.

## Section A

Body A line one.
Body A line two.

## Section B

Only B.

### Nested B1

Nested content.
"""


def test_split_markdown_sections_yields_heading_chunks() -> None:
    sections = import_md.split_markdown_sections(SAMPLE)
    paths = [s.heading_path for s in sections]
    assert ("Top level",) in paths
    assert ("Top level", "Section A") in paths
    assert ("Top level", "Section B") in paths
    assert ("Top level", "Section B", "Nested B1") in paths


def test_preamble_before_first_heading() -> None:
    sections = import_md.split_markdown_sections(SAMPLE)
    preambles = [s for s in sections if not s.heading_path]
    assert len(preambles) == 1
    assert "Preamble paragraph" in preambles[0].body


def test_render_section_text_includes_heading_breadcrumb() -> None:
    sections = import_md.split_markdown_sections(SAMPLE)
    sec_a = next(s for s in sections if s.heading_path == ("Top level", "Section A"))
    text = import_md.render_section_text(sec_a)
    assert text.startswith("Top level > Section A")
    assert "Body A line one" in text


def test_external_id_is_stable_for_path_and_headings() -> None:
    eid = import_md.external_id_for_section(
        "docs/decisions/037-foo.md",
        ("Top level", "Section A"),
    )
    assert eid.startswith("migration:md:")
    again = import_md.external_id_for_section(
        "docs/decisions/037-foo.md",
        ("Top level", "Section A"),
    )
    assert eid == again


def test_section_to_fact_matches_bulk_seed_contract() -> None:
    sections = import_md.split_markdown_sections(SAMPLE)
    sec = next(s for s in sections if s.heading_path == ("Top level", "Section B"))
    fact = import_md.section_to_fact(
        sec,
        source_path="docs/decisions/sample.md",
        event_date="2026-06-01",
        source="cursor-repo",
    )
    assert fact["infer"] is False
    assert fact["metadata"]["type"] == "fact"
    assert fact["metadata"]["event_date"] == "2026-06-01"
    assert fact["metadata"]["source_doc_id"] == "docs/decisions/sample.md"
    assert fact["external_id"].startswith("migration:md:")


def test_parse_markdown_file(tmp_path: Path) -> None:
    md = tmp_path / "note.md"
    md.write_text("# Hello\n\nWorld.\n", encoding="utf-8")
    facts = import_md.parse_markdown_file(
        md,
        event_date="2026-06-11",
        source="manual",
    )
    assert len(facts) == 1
    assert "Hello" in facts[0]["text"]
    assert facts[0]["metadata"]["source"] == "manual"


def test_parse_markdown_file_uses_mtime_when_no_event_date(tmp_path: Path) -> None:
    md = tmp_path / "dated.md"
    md.write_text("# Dated\n\nContent.\n", encoding="utf-8")
    facts = import_md.parse_markdown_file(md)
    expected = _dt.date.fromtimestamp(md.stat().st_mtime).isoformat()
    assert facts[0]["metadata"]["event_date"] == expected
