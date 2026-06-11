"""Unit tests for migration dedup (ADR 037 external_id + normalized text)."""

from __future__ import annotations

from migration import dedup


def _fact(
    *,
    external_id: str,
    text: str,
) -> dict[str, object]:
    return {
        "external_id": external_id,
        "text": text,
        "metadata": {
            "type": "fact",
            "source": "cursor-repo",
            "event_date": "2026-06-11",
        },
        "infer": False,
    }


def _bank_record(
    *,
    external_id: str | None = None,
    text: str,
) -> dict[str, object]:
    meta: dict[str, object] = {"type": "fact"}
    if external_id:
        meta["external_id"] = external_id
    return {"memory": text, "metadata": meta}


def test_normalize_text_collapses_whitespace_and_case() -> None:
    assert dedup.normalize_text("  Hello   World \n") == "hello world"


def test_build_bank_index_collects_external_ids_and_text() -> None:
    index = dedup.build_bank_index(
        [
            _bank_record(external_id="seed:a", text="Alpha fact."),
            _bank_record(text="Beta fact."),
        ]
    )
    assert "seed:a" in index.external_ids
    assert "beta fact." in index.normalized_texts


def test_filter_new_facts_drops_existing_external_id() -> None:
    bank = [_bank_record(external_id="seed:exists", text="Already stored.")]
    facts = [_fact(external_id="seed:exists", text="New wording.")]
    result = dedup.filter_new_facts(facts, bank)
    assert result.kept == []
    assert len(result.dropped) == 1
    assert result.dropped[0].reason == "external_id"
    assert result.dropped[0].fact["external_id"] == "seed:exists"


def test_filter_new_facts_drops_existing_normalized_text() -> None:
    bank = [_bank_record(external_id="seed:old", text="Same body text.")]
    facts = [_fact(external_id="seed:new", text="Same   BODY\nText.")]
    result = dedup.filter_new_facts(facts, bank)
    assert result.kept == []
    assert result.dropped[0].reason == "text"


def test_filter_new_facts_keeps_genuinely_new_facts() -> None:
    bank = [_bank_record(external_id="seed:old", text="Existing memory.")]
    facts = [_fact(external_id="seed:new", text="Brand-new content.")]
    result = dedup.filter_new_facts(facts, bank)
    assert len(result.kept) == 1
    assert result.kept[0]["external_id"] == "seed:new"
    assert result.dropped == []


def test_filter_new_facts_dedupes_within_batch_by_text() -> None:
    facts = [
        _fact(external_id="seed:a", text="Duplicate paragraph."),
        _fact(external_id="seed:b", text="Duplicate   paragraph."),
    ]
    result = dedup.filter_new_facts(facts, [])
    assert len(result.kept) == 1
    assert result.kept[0]["external_id"] == "seed:a"
    assert result.dropped[0].reason == "text"
    assert result.dropped[0].fact["external_id"] == "seed:b"


def test_filter_new_facts_dedupes_within_batch_by_external_id() -> None:
    facts = [
        _fact(external_id="seed:same", text="First version."),
        _fact(external_id="seed:same", text="Second version."),
    ]
    result = dedup.filter_new_facts(facts, [])
    assert len(result.kept) == 1
    assert result.kept[0]["text"] == "First version."
    assert result.dropped[0].reason == "external_id"


def test_dedup_facts_returns_only_kept_list() -> None:
    bank = [_bank_record(external_id="seed:skip", text="Skip me.")]
    facts = [
        _fact(external_id="seed:skip", text="Skip me."),
        _fact(external_id="seed:keep", text="Keep me."),
    ]
    kept = dedup.dedup_facts(facts, bank)
    assert len(kept) == 1
    assert kept[0]["external_id"] == "seed:keep"
