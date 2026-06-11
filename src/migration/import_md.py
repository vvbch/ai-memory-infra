"""Parse markdown files into bulk-seed facts (Phase 5)."""

from __future__ import annotations

import datetime as _dt
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from memory.contract import DEFAULT_NAMESPACE, TYPE_FACT

_HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
_SLUG_RE = re.compile(r"[^a-z0-9]+")


@dataclass(frozen=True)
class MarkdownSection:
    """One chunk of markdown under a heading path (empty tuple = preamble)."""

    heading_path: tuple[str, ...]
    body: str
    level: int


def split_markdown_sections(markdown: str) -> list[MarkdownSection]:
    """Split markdown on ATX headings (# .. ######)."""
    sections: list[MarkdownSection] = []
    stack: list[tuple[int, str]] = []
    body_lines: list[str] = []

    def flush() -> None:
        body = "\n".join(body_lines).strip()
        if not body and not stack:
            body_lines.clear()
            return
        if not body:
            body_lines.clear()
            return
        path = tuple(title for _, title in stack)
        level = stack[-1][0] if stack else 0
        sections.append(MarkdownSection(heading_path=path, body=body, level=level))
        body_lines.clear()

    for line in markdown.splitlines():
        match = _HEADING_RE.match(line)
        if match:
            flush()
            level = len(match.group(1))
            title = match.group(2).strip()
            while stack and stack[-1][0] >= level:
                stack.pop()
            stack.append((level, title))
            continue
        body_lines.append(line)

    flush()
    return sections


def render_section_text(section: MarkdownSection) -> str:
    """Render section body with heading breadcrumb for retrieval context."""
    body = section.body.strip()
    if not section.heading_path:
        return body
    prefix = " > ".join(section.heading_path)
    return f"{prefix}\n\n{body}".strip()


def _slugify(value: str, *, max_len: int = 48) -> str:
    slug = _SLUG_RE.sub("-", value.lower()).strip("-")
    return slug[:max_len] or "section"


def external_id_for_section(source_path: str, heading_path: tuple[str, ...]) -> str:
    """Deterministic external_id for a file section."""
    posix = Path(source_path).as_posix().replace("/", ":")
    parts = ["migration:md", posix]
    for title in heading_path:
        parts.append(_slugify(title))
    if not heading_path:
        parts.append("preamble")
    external_id = ":".join(parts)
    return external_id[:240]


def section_to_fact(
    section: MarkdownSection,
    *,
    source_path: str,
    event_date: str,
    source: str = "cursor-repo",
    namespace: str = DEFAULT_NAMESPACE,
) -> dict[str, Any]:
    """Convert a parsed section to bulk_seed_importer fact dict."""
    text = render_section_text(section)
    return {
        "external_id": external_id_for_section(source_path, section.heading_path),
        "text": text,
        "metadata": {
            "type": TYPE_FACT,
            "source": source,
            "event_date": event_date,
            "namespace": namespace,
            "source_doc_id": Path(source_path).as_posix(),
        },
        "infer": False,
    }


def parse_markdown_text(
    markdown: str,
    *,
    source_path: str,
    event_date: str | None = None,
    source: str = "cursor-repo",
) -> list[dict[str, Any]]:
    """Parse markdown string into fact dicts."""
    resolved_date = event_date or _dt.date.today().isoformat()
    facts: list[dict[str, Any]] = []
    for section in split_markdown_sections(markdown):
        if not render_section_text(section).strip():
            continue
        facts.append(
            section_to_fact(
                section,
                source_path=source_path,
                event_date=resolved_date,
                source=source,
            )
        )
    return facts


def parse_markdown_file(
    path: str | Path,
    *,
    event_date: str | None = None,
    source: str = "cursor-repo",
) -> list[dict[str, Any]]:
    """Read a markdown file and return bulk-seed fact dicts."""
    file_path = Path(path)
    text = file_path.read_text(encoding="utf-8")
    if event_date is None:
        event_date = _dt.date.fromtimestamp(file_path.stat().st_mtime).isoformat()
    return parse_markdown_text(
        text,
        source_path=file_path.as_posix(),
        event_date=event_date,
        source=source,
    )
