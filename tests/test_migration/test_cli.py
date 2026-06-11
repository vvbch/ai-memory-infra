"""Unit tests for migration CLI dry-run."""

from __future__ import annotations

import json
from pathlib import Path

from click.testing import CliRunner

from migration.cli import (
    collect_markdown_files,
    format_report,
    main,
    run_import_pipeline,
    write_facts_json,
)


def test_collect_markdown_files_finds_nested_md(tmp_path: Path) -> None:
    nested = tmp_path / "sub"
    nested.mkdir()
    (tmp_path / "a.md").write_text("# A\n", encoding="utf-8")
    (nested / "b.md").write_text("# B\n", encoding="utf-8")
    (tmp_path / "ignore.txt").write_text("nope", encoding="utf-8")
    paths = collect_markdown_files(tmp_path)
    assert [p.name for p in paths] == ["a.md", "b.md"]


def test_run_import_pipeline_wires_parse_categorize_dedup(tmp_path: Path) -> None:
    docs = tmp_path / "docs" / "decisions"
    docs.mkdir(parents=True)
    (docs / "037-sample.md").write_text(
        "# ADR 037\n\nWrite-path idempotency contract.\n",
        encoding="utf-8",
    )
    report = run_import_pipeline(docs, bank_records=[], sample_size=3)
    assert report.files_scanned == 1
    assert report.parsed_count == 1
    assert report.kept_count == 1
    assert report.dropped_count == 0
    assert report.sample_external_ids[0].startswith("migration:md:")
    assert "037-sample" in report.sample_external_ids[0]


def test_run_import_pipeline_dedupes_against_bank(tmp_path: Path) -> None:
    (tmp_path / "note.md").write_text("# Hello\n\nWorld.\n", encoding="utf-8")
    bank = [{"memory": "Hello\n\nWorld.", "metadata": {"external_id": "seed:old"}}]
    report = run_import_pipeline(tmp_path, bank_records=bank)
    assert report.parsed_count == 1
    assert report.kept_count == 0
    assert report.dropped_count == 1


def test_format_report_includes_counts_and_samples() -> None:
    from migration.cli import ImportReport

    report = ImportReport(
        source=Path("docs/decisions"),
        files_scanned=2,
        parsed_count=5,
        kept_count=4,
        dropped_count=1,
        sample_external_ids=("migration:md:foo:bar",),
        dropped=(),
    )
    text = format_report(report, dry_run=True)
    assert "dry-run" in text
    assert "Files scanned: 2" in text
    assert "Parsed chunks: 5" in text
    assert "After dedup: 4 (dropped 1)" in text
    assert "migration:md:foo:bar" in text


def test_import_dry_run_cli_prints_summary(tmp_path: Path) -> None:
    (tmp_path / "sample.md").write_text("# Title\n\nBody.\n", encoding="utf-8")
    runner = CliRunner()
    result = runner.invoke(
        main,
        ["import", "--source", str(tmp_path), "--dry-run"],
    )
    assert result.exit_code == 0, result.output
    assert "Migration import (dry-run)" in result.output
    assert "Parsed chunks: 1" in result.output
    assert "migration:md:" in result.output


def test_import_without_dry_run_rejected(tmp_path: Path) -> None:
    runner = CliRunner()
    result = runner.invoke(main, ["import", "--source", str(tmp_path)])
    assert result.exit_code != 0
    assert "Live import is not enabled" in result.output


def test_import_cmd_registered_on_main() -> None:
    command = main.get_command(None, "import")
    assert command is not None
    assert command.name == "import"


def test_write_facts_json_matches_bulk_seed_shape(tmp_path: Path) -> None:
    facts = [
        {
            "external_id": "migration:md:sample:hello",
            "text": "Hello",
            "metadata": {
                "type": "fact",
                "source": "cursor-repo",
                "event_date": "2026-06-01",
                "namespace": "public",
            },
            "infer": False,
        }
    ]
    out = tmp_path / "facts.json"
    write_facts_json(out, facts)
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload["facts"][0]["external_id"] == "migration:md:sample:hello"


def test_import_dry_run_writes_output_json(tmp_path: Path) -> None:
    (tmp_path / "sample.md").write_text("# Title\n\nBody.\n", encoding="utf-8")
    out = tmp_path / "out.json"
    runner = CliRunner()
    result = runner.invoke(
        main,
        ["import", "--source", str(tmp_path), "--dry-run", "--output", str(out)],
    )
    assert result.exit_code == 0, result.output
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert len(payload["facts"]) == 1
    assert "Wrote 1 facts" in result.output
