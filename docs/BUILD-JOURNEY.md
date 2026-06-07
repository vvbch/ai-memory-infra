# Build Journey — how this was built (public summary)

> A curated, session-by-session summary of how this infrastructure was built —
> milestones, key decisions, and rough effort. Distilled from a detailed private
> build log; **decisions** live in `docs/decisions/` (ADRs), the **current state**
> in `docs/planning/STATUS.md`, and the **how-to** in `docs/setup.md`.
>
> Append-only. Personal/operational detail is deliberately omitted.

---

## 2026-06-07 — Accounts, domain & secrets for Phase-1 deploy

**Focus:** stand up the external accounts, domain, and secrets needed before
`terraform apply` (Phase 1). **Effort:** ~80 min (single collaborative session).

**Milestones**
- Credential vault + **time-delayed nominee handoff** set up (Bitwarden Emergency
  Access), with a verified design fix: secrets must live in the *individual* vault,
  not a shared collection, or the handoff silently fails.
- Domain **`chandrav.dev`** registered with privacy redaction; 10-year registration.
- Cloud account + billing + a spend **alert** in place; all provider API
  credentials generated under **least-privilege, zone/scope-bound** where possible.

**Decisions**
- **ADR 019** — compute provider (DigitalOcean droplet, Bangalore) chosen over
  AWS/GCP/Azure/Hetzner on cost-floor + India latency + clean exit; single-node by
  design, with graceful degradation covering outages.
- **Tenet 15** — prefer fixed, capped cost over variable on-demand pricing, even at
  a mild premium; hard caps + billing alerts on anything usage-based.
- **Credential-custody gate** — every account/token/key is stored in the vault as
  it's created; never in the repo or chat (extends ADR 017).

**Engineering notes**
- Verified each volatile fact before baking it in (Bitwarden emergency-access scope,
  Cloudflare multi-year registration, live VPS pricing, Cloudflare-vs-VM capability).
- Caught two silent-failure traps before they bit (vault-scope; a changed provider
  console flow) and turned recurring questions into durable tenets/ADRs.
