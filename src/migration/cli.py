"""Click CLI for the migration pipeline (Phase 5)."""

from __future__ import annotations

import datetime as _dt
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import click

from migration import categorizer, dedup, import_md
from migration.dedup import DroppedFact

DEFAULT_SOURCE = "cursor-repo"


@dataclass(frozen=True)
class ImportReport:
    """Summary of a migration import run."""

    source: Path
    files_scanned: int
    parsed_count: int
    kept_count: int
    dropped_count: int
    sample_external_ids: tuple[str, ...]
    dropped: tuple[DroppedFact, ...]


def collect_markdown_files(source: Path) -> list[Path]:
    """Return sorted ``.md`` files under *source* (recursive)."""
    root = source.resolve()
    return sorted(path for path in root.rglob("*.md") if path.is_file())


def facts_from_file(
    path: Path,
    source_root: Path,
    *,
    source: str = DEFAULT_SOURCE,
) -> list[dict[str, Any]]:
    """Parse one markdown file using paths relative to *source_root*."""
    root = source_root.resolve()
    rel = path.resolve().relative_to(root).as_posix()
    text = path.read_text(encoding="utf-8")
    event_date = _dt.date.fromtimestamp(path.stat().st_mtime).isoformat()
    return import_md.parse_markdown_text(
        text,
        source_path=rel,
        event_date=event_date,
        source=source,
    )


def run_import_pipeline(
    source: Path,
    *,
    bank_records: list[dict[str, Any]] | None = None,
    sample_size: int = 5,
    source_tag: str = DEFAULT_SOURCE,
) -> ImportReport:
    """import_md → categorizer → dedup over all markdown under *source*."""
    root = source.resolve()
    files = collect_markdown_files(root)
    parsed: list[dict[str, Any]] = []
    for path in files:
        parsed.extend(facts_from_file(path, root, source=source_tag))

    categorized = categorizer.categorize_facts(parsed)
    result = dedup.filter_new_facts(categorized, bank_records or [])
    sample = tuple(fact["external_id"] for fact in result.kept[:sample_size])

    return ImportReport(
        source=root,
        files_scanned=len(files),
        parsed_count=len(parsed),
        kept_count=len(result.kept),
        dropped_count=len(result.dropped),
        sample_external_ids=sample,
        dropped=tuple(result.dropped),
    )


def format_report(report: ImportReport, *, dry_run: bool) -> str:
    """Human-readable summary for stdout."""
    mode = "dry-run" if dry_run else "live"
    lines = [
        f"Migration import ({mode})",
        f"Source: {report.source}",
        f"Files scanned: {report.files_scanned}",
        f"Parsed chunks: {report.parsed_count}",
        f"After dedup: {report.kept_count} (dropped {report.dropped_count})",
    ]
    if report.sample_external_ids:
        lines.append("Sample external_ids:")
        lines.extend(f"  - {external_id}" for external_id in report.sample_external_ids)
    return "\n".join(lines)


def load_bank_records() -> list[dict[str, Any]]:
    """Fetch existing memories from the live API for dedup."""
    from mcp_proxy.client import MemoryApiClient, MemoryApiConfig
    from mcp_proxy.idempotent_write import list_all_memories

    client = MemoryApiClient(MemoryApiConfig.from_env())
    return list_all_memories(client)


@click.group()
def main() -> None:
    """Import local markdown into the memory bank."""


@main.command("import")
@click.option(
    "--source",
    required=True,
    type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path),
    help="Directory of markdown files to import.",
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Parse, classify, and dedup only — no live write.",
)
@click.option(
    "--sample",
    default=5,
    show_default=True,
    help="Number of sample external_ids to print.",
)
@click.option(
    "--use-bank",
    is_flag=True,
    help="Dedup against the live memory bank (requires API credentials).",
)
def import_cmd(
    source: Path,
    dry_run: bool,
    sample: int,
    use_bank: bool,
) -> None:
    """Run import_md → categorizer → dedup over a docs directory."""
    if not dry_run:
        raise click.ClickException(
            "Live import is not enabled yet; re-run with --dry-run or use "
            "scripts/bulk_seed_importer.py after exporting facts to JSON."
        )

    bank_records = load_bank_records() if use_bank else []
    report = run_import_pipeline(source, bank_records=bank_records, sample_size=sample)
    click.echo(format_report(report, dry_run=True))
