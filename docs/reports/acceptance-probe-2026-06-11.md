# Acceptance probe results

**Overall:** PASS

## backdated_recency — PASS
- Expected: max event_date -> implementation started (2026-06-10)
- latest_text: Project Alpha status: implementation started
- candidate_count: 3

## structured_filter — PASS
- Expected: open_item metadata filter returns probe follow-up
- metadata_filter_hit: True
- pure_vector_hit: True
- note: Pure vector search alone may miss open items — metadata filter required (documented contract limit).

## entity_collision — PASS
- Expected: Among Jordan hits, inline qualifier rerank picks project contact, not team lead's sibling
- best_jordan_text: Follow up with Jordan, project contact, about system design mock
- top_texts: ['Project Alpha status: implementation started', 'Project Alpha status: cancelled', 'Project Alpha status: planning phase', 'Follow up with Jordan, project contact, about system design mock', "Jordan, team lead's sibling, started summer coding camp"]
- jordan_hit_count: 3

Deleted 6 probe memories.