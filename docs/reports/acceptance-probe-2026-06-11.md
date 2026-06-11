# Acceptance probe results

**Overall:** PASS

**Date:** 2026-06-11  
**Bank:** `user_id=primary-user` @ `https://memory.example.com`  
**Script:** `scripts/acceptance_probe.py`

## backdated_recency — PASS

- Expected: max event_date -> implementation started (2026-06-10)
- latest_text: Project Alpha status: implementation started
- candidate_count: 3

Backdated cancel fact (event_date 2026-05-15, written after newer rows) did not win.

## structured_filter — PASS

- Expected: open_item metadata filter returns probe follow-up
- metadata_filter_hit: True
- pure_vector_hit: True (also matched on this run; not relied upon)
- note: Pure vector search alone may miss open items — metadata filter required (documented contract limit).

## entity_collision — PASS

- Expected: Among Jordan hits, inline qualifier rerank picks project contact, not team lead's sibling
- best_Jordan_text: Follow up with Jordan, project contact, about system design mock
- Jordan_hit_count: 3

Pure vector top-5 included elder-son fact; contract read path (`best_entity_match`) disambiguated correctly.

## Cleanup

Deleted 6 probe memories after queries.

## Gate

Bulk fact load may proceed in a separate seed session.
