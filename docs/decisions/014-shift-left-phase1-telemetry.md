# ADR 014: Bounded shift-left — minimal telemetry in Phase 1

**Status:** Accepted
**Date:** 2026-06-06
**Deciders:** the operator

### Context

Observability is its own phase (Phase 8: Prometheus + Grafana dashboards, drift
detection, alert rules). The eval framework is Phase 7. On a solo project it is
tempting to defer *all* measurement to those phases — but that creates two
problems:

1. **No baseline.** If extraction/retrieval are unmeasured from Phase 1 → Phase
   7/8, there is no early data to compare against; you can't detect drift you
   never recorded, and the first eval run has nothing historical to anchor to.
2. **Retrofit risk.** Bolting telemetry onto a finished system is a bigger,
   riskier change than emitting a few signals from the start. This is the
   shift-left principle: build quality in per-phase, don't append it.

The counter-risk is **over-engineering early** — standing up the full
observability stack in Phase 1 would violate Tenet 7 (fewer moving parts) and
delay the actual infra (Terraform/Compose/Caddy).

So the question is **how much** telemetry belongs in Phase 1 — not whether.

### Decision

Add a **bounded** set of telemetry hooks in Phase 1, and **explicitly defer** the
heavy observability work to Phases 7/8.

**In Phase 1 (build now, before `variables.tf` resumes):**

1. **A `/metrics` endpoint** exposing:
   - retrieval latency and extraction latency,
   - memory count by category (the venture tags: `trading_firm`, `social_media`,
     `ria`, `personal`, `career`, `migration`).
   Prometheus-scrapeable shape, so Phase 8 just points Prometheus at it — no
   re-instrumentation.
2. **An extraction log line per extraction**, capturing: input (the snippet),
   output (the extracted facts), **model id**, token counts, and timestamp. This
   is the **raw material for future drift detection** — you cannot baseline drift
   you never logged.

**Deferred to Phases 7/8 (do NOT build in Phase 1):**

- Grafana dashboards and panels (Phase 8).
- Drift *baselines* and the weekly drift detector (Phase 7/8) — Phase 1 only
  *captures* the data they will later consume.
- Cross-LLM cost-vs-quality comparison (Phase 7 eval framework).
- Alert rules (Phase 8).

### Boundary (why this is "bounded", not scope creep)

Phase 1 emits **signals** (an endpoint + a structured log). Phases 7/8 build the
**systems that consume them** (dashboards, baselines, comparisons, alerts).
Emitting a metric is cheap and forward-compatible; the expensive, design-heavy
consumption work stays in its proper phase. If a hook starts to require its own
storage, UI, or scheduled job, it has crossed the line and belongs in 7/8.

### Consequences

- **Positive:** Phase 7/8 become *consolidation* (wire up data that already
  flows) rather than *construction*; an extraction log exists from day one for
  drift/audit; the `/metrics` contract is set early so the Prometheus wiring is
  trivial later. Clean portfolio narrative ("quality built in per-phase, not
  retrofitted").
- **Negative:** a small amount of Phase-1 work that doesn't pay off until later
  phases; the log format must be chosen with enough foresight that Phase 7 can
  use it without a schema change (mitigated: log input/output/model/tokens/ts —
  the fields drift detection needs).
- **Cross-refs:** AGENTS.md build phases + engineering practices; ADR 007 (eval
  framework, the Phase-7 consumer); ADR 008 (observability stack, the Phase-8
  consumer); `interview_packet.md` §6 "shift-left" highlight + STAR entry.

---
