# Backlog — prioritized, deferred work

> Parked-but-valuable work, ranked. Captured so nothing is lost and nothing
> silently displaces the current goal (tenet 13). `STATUS.md` "Next action" is what
> we're doing *now*; this is what we've consciously chosen to do *later*.
>
> **Priorities:** **P1** = do at the next natural opportunity (security / soon-blocking).
> **P2** = governance/quality hardening, fold into the relevant phase. **P3** =
> valuable but non-blocking / personal.

## P1 — do at the start of Phase-1 CI work

- **Secret-scan pre-commit (e.g. gitleaks).** Make "no secrets in git" a
  *deterministic gate*, not just a prose rule — relevant now that we handle DO /
  Cloudflare / OpenAI tokens. Ties: AGENTS.md secrets rule, tenet 14 (Detect layer).

## P2 — governance & quality hardening (fold into CI / eval phases)

- **Policy-as-code for pointer files (ADR 018 enforcement).** Either *generate*
  `.cursor/rules/*` + `CLAUDE.md` from `AGENTS.md` (propagation by definition →
  drift impossible by construction), and/or a **pointer-lint** that fails if a
  pointer file carries tenet/rule content. Closes the COE detection gap
  (`docs/coe/2026-06-07-cursor-rule-drift.md`).
- **Behavioural tenets as eval/CI checks** where feasible — codify rules that have
  teeth as tests that block on regression (tenet 14).

## P3 — valuable, non-blocking / personal

- **Bitwarden full family rollout.** Families plan already paid (2026-06-07).
  Remaining: invite the (up to 6) members, migrate passwords off Gmail/WhatsApp
  into shared collections, set per-member access (ADR 017 / `financial-decisions.md`).
- **KeePassXC offline vault backup** (`.kdbx` in a safe / will) as a
  vendor-independent fallback (ADR 017 "secondary backup").
