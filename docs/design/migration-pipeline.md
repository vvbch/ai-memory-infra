# Migration pipeline (Phase 5)

> Short design for importing local markdown (and later Google Drive exports) into
> the curated memory bank via the ADR 037 write contract — **not** via raw MCP
> retries.

## Goal

Turn filesystem sources into idempotent bulk-seed facts:

```text
.md / .mdx files  →  import_md (parse)  →  categorizer (ventures)  →  dedup (filter)
       →  bulk_seed_importer / csv_to_bulk_seed contract
```

Bulk load from `data/reconciled-facts.csv` remains the operator-curated path;
migration is for **automated** imports from docs with stable `external_id`s.

## Stages

| Stage | Module | Job |
|-------|--------|-----|
| 1. Parse | `import_md.py` | Split on ATX headings; one fact per section; `source_doc_id` = file path |
| 2. Classify | `categorizer.py` | Tag `ventures` from path/keywords (ADR 003) |
| 3. Dedup | `dedup.py` | Drop chunks whose `external_id` or normalized text already in bank |
| 4. Load | `bulk_seed_importer.py` | Idempotent write (`infer=false` default for authored chunks) |

## Fact shape (per section)

- `external_id`: `migration:md:{posix-path}:{heading-slug...}`
- `text`: heading breadcrumb + body (so retrieval sees context)
- `metadata.event_date`: file mtime or frontmatter (later); default file date
- `metadata.source`: `cursor-repo` for repo docs, `manual` for imports
- `metadata.source_doc_id`: relative path from import root
- `metadata.namespace`: `public` unless path matches sensitive prefix (later)
- `infer`: `false` (verbatim chunks)

## Out of scope (this phase)

- LifeGraph / Neo4j writes
- Live Mem0 `infer=true` extraction during migration
- Google Drive API (`import_gdrive.py` stub only)
- Production bulk run until operator approves dry-run output

## Verification

1. Unit: `tests/test_migration/test_import_md.py`
2. Dry-run: `python -m migration import --source ./docs/decisions/ --dry-run` (CLI later)
3. Compare chunk count + sample `external_id`s before any live write
