from __future__ import annotations

import importlib.util
import json
import pathlib
import tempfile

_CSV_TOOL = pathlib.Path(__file__).resolve().parents[2] / "scripts" / "csv_to_bulk_seed.py"
_spec = importlib.util.spec_from_file_location("csv_to_bulk_seed", _CSV_TOOL)
assert _spec and _spec.loader
csv_to_bulk_seed = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(csv_to_bulk_seed)
csv_to_facts = csv_to_bulk_seed.csv_to_facts


def test_csv_to_facts_skips_example_rows() -> None:
    csv_text = """external_id,text,event_date,source,namespace
example:skip,"Jordan, project contact, is a contact",2026-06-01,manual,public
seed:real,"Alex prefers Python over shell",2026-06-02,cursor-repo,public
"""
    with tempfile.NamedTemporaryFile("w", suffix=".csv", delete=False, encoding="utf-8") as fh:
        fh.write(csv_text)
        path = pathlib.Path(fh.name)
    try:
        facts = csv_to_facts(path)
    finally:
        path.unlink()
    assert len(facts) == 1
    assert facts[0]["external_id"] == "seed:real"
    assert facts[0]["metadata"]["event_date"] == "2026-06-02"
    assert facts[0]["infer"] is False


def test_main_writes_json() -> None:
    csv_text = """external_id,text,event_date,source
seed:a,"Jordan, team lead's sibling, likes coding",2026-06-01,manual
"""
    with tempfile.TemporaryDirectory() as tmp:
        csv_path = pathlib.Path(tmp) / "facts.csv"
        out_path = pathlib.Path(tmp) / "facts.json"
        csv_path.write_text(csv_text, encoding="utf-8")
        rc = csv_to_bulk_seed.main([str(csv_path), "-o", str(out_path)])
        assert rc == 0
        payload = json.loads(out_path.read_text(encoding="utf-8"))
        assert len(payload["facts"]) == 1
