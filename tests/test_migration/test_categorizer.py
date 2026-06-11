"""Unit tests for venture tagging (ADR 003 paths/keywords)."""

from __future__ import annotations

from migration import categorizer


def test_infer_ventures_from_trading_path() -> None:
    tags = categorizer.infer_ventures(
        source_path="ventures/alpha-corp/strategy.md",
        text="Quarterly rebalance notes.",
    )
    assert tags == ["trading_firm"]


def test_infer_ventures_from_social_media_path() -> None:
    tags = categorizer.infer_ventures(
        source_path="notes/social-media/content-plan.md",
        text="Content calendar.",
    )
    assert tags == ["social_media"]


def test_infer_ventures_from_trading_keywords_in_text() -> None:
    tags = categorizer.infer_ventures(
        source_path="inbox/scratch.md",
        text="Equity desk derivatives strategy with portfolio rebalance.",
    )
    assert tags == ["trading_firm"]


def test_infer_ventures_from_career_keywords() -> None:
    tags = categorizer.infer_ventures(
        source_path="inbox/todo.md",
        text="Follow up on hiring pipeline interview prep.",
    )
    assert tags == ["career"]


def test_infer_ventures_from_migration_path_and_keywords() -> None:
    tags = categorizer.infer_ventures(
        source_path="career/relocation/timeline.md",
        text="Work visa milestones and international relocation backup plan.",
    )
    assert tags == ["career", "migration"]


def test_infer_ventures_for_infra_decision_docs() -> None:
    tags = categorizer.infer_ventures(
        source_path="docs/decisions/037-write-path-idempotency-and-dedup-contract.md",
        text="ADR 037 locks the bulk write contract.",
    )
    assert tags == ["personal"]


def test_infer_ventures_for_migration_pipeline_code() -> None:
    tags = categorizer.infer_ventures(
        source_path="src/migration/import_md.py",
        text="Parse markdown files into bulk-seed facts.",
    )
    assert tags == ["migration"]


def test_infer_ventures_returns_empty_when_no_signal() -> None:
    tags = categorizer.infer_ventures(
        source_path="tmp/notes.md",
        text="Generic note with no venture cues.",
    )
    assert tags == []


def test_categorize_fact_adds_ventures_to_metadata() -> None:
    fact = {
        "external_id": "migration:md:docs:decisions:sample:preamble",
        "text": "Portfolio rebalance rollout checklist.",
        "metadata": {
            "type": "fact",
            "source": "cursor-repo",
            "event_date": "2026-06-11",
            "source_doc_id": "ventures/alpha-corp/checklist.md",
        },
        "infer": False,
    }
    out = categorizer.categorize_fact(fact)
    assert out["metadata"]["ventures"] == ["trading_firm"]
    assert out["external_id"] == fact["external_id"]
    assert out is not fact
    assert out["metadata"] is not fact["metadata"]


def test_categorize_fact_preserves_existing_ventures() -> None:
    fact = {
        "external_id": "seed:manual:1",
        "text": "Hiring pipeline follow-up.",
        "metadata": {
            "type": "fact",
            "source": "manual",
            "event_date": "2026-06-11",
            "ventures": ["career"],
        },
        "infer": False,
    }
    out = categorizer.categorize_fact(fact)
    assert out["metadata"]["ventures"] == ["career"]


def test_categorize_facts_batch() -> None:
    facts = [
        {
            "external_id": "a",
            "text": "Video production content plan.",
            "metadata": {
                "type": "fact",
                "source": "manual",
                "event_date": "2026-06-11",
                "source_doc_id": "notes/social-media/plan.md",
            },
            "infer": False,
        },
        {
            "external_id": "b",
            "text": "Fiduciary registration research.",
            "metadata": {
                "type": "fact",
                "source": "manual",
                "event_date": "2026-06-11",
                "source_doc_id": "ventures/advisory/overview.md",
            },
            "infer": False,
        },
    ]
    out = categorizer.categorize_facts(facts)
    assert out[0]["metadata"]["ventures"] == ["social_media"]
    assert out[1]["metadata"]["ventures"] == ["ria"]
