# Build Journey — how this was built (public summary)

> A curated, session-by-session summary of how this infrastructure was built —
> milestones, key decisions, and rough effort. Distilled from a detailed private
> build log; **decisions** live in `docs/decisions/` (ADRs), the **current state**
> in `docs/planning/STATUS.md`, and the **how-to** in `docs/setup.md`.
>
> Append-only. Personal/operational detail is deliberately omitted.

---

## 2026-06-08 — Made the deployed API usable (auth verified)

**Focus:** turn the live-but-locked memory API into a usable one. Short, single-task
session (concierge mode).

**Milestones**
- **API authentication verified working.** Auth is on by default; confirmed a protected
  endpoint returns *unauthorized* with no key and *success* when the admin API key is
  presented. The deploy was already usable — the key had been generated into the server
  config at deploy time — so no extra setup tooling or admin dashboard was needed.

**Decisions**
- **Used the simplest auth path that worked (fewer moving parts).** Rather than running the
  upstream "bootstrap" helper — which would have spun up a *second, conflicting* container
  stack — we used the shared admin key already wired into our own stack. Per-user keys and
  the setup wizard remain available if/when the admin dashboard is added later.

**Engineering notes**
- Caught that a documented "create admin" shortcut assumed the project's *default* layout, not
  our custom one — verifying against the actual running stack avoided standing up a duplicate
  database. Corrected a stale planning note (work flagged as "to commit" had already shipped a
  session earlier) so the resume state matches reality.

## 2026-06-08 — Control-plane: stateless, checkpointed agent sessions

**Focus:** a governance fix, no build state changed. A long-lived AI-agent session had
burned through a month's tooling-credit budget in about half a day; root-caused and fixed
the operating model rather than just buying more credits.

**Milestones**
- New **tenet: sessions are stateless and disposable** — one task per session, state
  checkpointed to the repo after every step, and **every response ends with a copy-paste
  "resume" token** so a fresh session reconstructs full context with zero loss. The repo is
  the durable backing store; the chat is disposable compute (the Twelve-Factor
  stateless-process pattern applied to agent sessions).
- **Blameless COE** recorded: an LLM agent re-sends the whole conversation transcript each
  turn, so a long session's token cost grows **~quadratically** with its length
  (*context-window amplification*) — the mechanism behind the credit burn.

**Decisions**
- Treat the **agent session itself as a metered, usage-based resource** and bound it — the
  tooling analog of the project's "cap variable cost" tenet. The cost discipline had only ever
  been aimed at cloud/LLM-API spend; this extends it to the build tooling.

**Engineering notes**
- Named the **pattern** (stateless single-task sessions + checkpoint/restore + continuation
  token) and the **anti-pattern** (monolithic long-lived session) in standard terms so the
  lesson transfers. Control plane fixed first (tenet + working model + Definition of Done),
  then the practice adopted — detection of future overruns parked as a backlog item.

## 2026-06-07 — Accounts, domain & secrets for Phase-1 deploy

**Focus:** stand up the external accounts, domain, and secrets needed before
`terraform apply` (Phase 1). **Effort:** ~2 hr across two collaborative sessions;
**all 5 secret sets gathered** — Phase-1 prerequisites complete.

**Milestones**
- Credential vault + **time-delayed nominee handoff** set up (Bitwarden Emergency
  Access), with a verified design fix: secrets must live in the *individual* vault,
  not a shared collection, or the handoff silently fails.
- Domain **`chandrav.dev`** registered with privacy redaction; 10-year registration.
- Cloud account + billing + a spend **alert** in place; all provider API
  credentials generated under **least-privilege, zone/scope-bound** where possible.
- **Model-API billing** set up with a true hard cap — **prepaid credits + auto-recharge
  off** (the vendor's dashboard "limit" is only advisory), plus 80%/100% usage alerts.

**Decisions**
- **ADR 019** — compute provider (DigitalOcean droplet, Bangalore) chosen over
  AWS/GCP/Azure/Hetzner on cost-floor + India latency + clean exit; single-node by
  design, with graceful degradation covering outages.
- **Tenet 15** — prefer fixed, capped cost over variable on-demand pricing, even at
  a mild premium; hard caps + billing alerts on anything usage-based.
- **Credential-custody gate** — every account/token/key is stored in the vault as
  it's created; never in the repo or chat (extends ADR 017).
- **Landed-cost discipline (×1.3)** — sharpened tenet 6: budget on **total cost of
  ownership** (list price + ~18% GST + forex), not the vendor sticker. A single purchase
  revealed every estimate was ~30% optimistic; fixed the *estimating method*, not one
  number, and re-baselined the cost model.

**Engineering notes**
- Verified each volatile fact before baking it in (Bitwarden emergency-access scope,
  Cloudflare multi-year registration, live VPS pricing, OpenAI billing flow).
- Caught two silent-failure traps before they bit (vault-scope; a changed provider
  console flow) and turned recurring questions into durable tenets/ADRs.
- Held the critical path through a payment rabbit hole — parked a marginal
  card-optimization as a separate decision rather than letting it delay the deploy.
