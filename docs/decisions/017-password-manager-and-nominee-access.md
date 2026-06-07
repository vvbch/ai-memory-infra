# ADR 017: Password manager + nominee (emergency-access) strategy

**Status:** Accepted
**Date:** 2026-06-07
**Deciders:** Chandra

### Context

The estate/exit path (tenet 12, `docs/decommission.md`) assumes credentials live
in a password manager — *not* in either git repo — and that a **nominee** can get
in if Chandra can't. Three billable accounts must be reachable to stop all spend:
DigitalOcean, Cloudflare, OpenAI; plus the SSH private-key passphrase.

Hard constraints:

- **No secret ever enters a repo** (public or private). Git history is permanent,
  both repos are Google-Drive-synced (tenet 11 → many copies), and `AGENTS.md`
  forbids secrets in code/commits/logs. The private repo is therefore the right
  home for the *runbook*, never the *credentials*.
- A repo's access model (clone + share) is the opposite of what a secret needs, so
  "grant the nominee access via the private repo" is rejected for credentials. The
  nominee gets the **runbook** from the repo and the **credentials** from the
  password manager's emergency-access channel.

This is a tenet-12 vendor decision, so candidates are weighed on total cost (incl.
exit cost), portability/lock-in, reliability/track record, company viability, and
ecosystem. Facts below verified 2026-06-07 from each vendor's docs/pricing pages
(tenet 8).

### Options considered

| | Emergency / nominee handoff | Recurring cost | Lock-in / exit | Notes |
|---|---|---|---|---|
| **Bitwarden** (chosen) | **Built-in Emergency Access** (grantor needs Premium/Families; grantee can be **free**; View or **Takeover**, min 1-day wait; keeps working if it lapses) | $19.80/yr Premium · **$47.88/yr Families (chosen, ~₹330/mo)** | **Lowest** — open-source, **self-hostable**, standard export (JSON/CSV) | Cross-platform (tenet 3); cheapest credible option with a managed nominee handoff |
| 1Password | **No true emergency-access**; relies on the **Emergency Kit** PDF (self-recovery) + Family-plan account recovery (recoverer must be a family admin) | $35.88/yr indiv / $71.88/yr family; **no free tier** (14-day trial) | Proprietary; export exists but closed format | Best UX + Secret-Key model; but nominee path is a printed PDF, not a managed grant |
| Proton Pass | **Emergency Access** (since Aug 2025; up to 5 contacts, wait up to 30 days) — **but requires a Proton paid plan AND a Proton-address account**; won't work with an external email | Free tier (no emergency access); Pass Plus paid for it | E2EE, Swiss; export exists | The Proton-address caveat is a real gotcha for a Gmail-primary user |
| KeePassXC | **None built-in** — inheritance = hand the `.kdbx` file + master password to the nominee (sealed envelope / will / safe-deposit) | **₹0** (local file) | **Maximal portability** — open `.kdbx` format, no vendor | Most manual; worst fit for a *non-engineer* nominee (no guided takeover) → against the concierge/executor goal |

### Decision

**Adopt Bitwarden (Premium) as the credential vault, with Bitwarden Emergency
Access as the nominee handoff.**

1. One **individual-vault Folder** named `ai-memory-infra` holds: DigitalOcean,
   Cloudflare, OpenAI logins (+ 2FA where used), the SSH private-key passphrase, and
   **every other project credential as it is created** (API tokens, DO Spaces keys,
   etc.) — codified as a Definition-of-Done gate in `AGENTS.md`. For SSO logins
   (e.g. DigitalOcean via Google), store a note so the nominee knows the path in.
   **It must be an individual-vault Folder, NOT a Families/Organization
   Collection:** Bitwarden Emergency Access (incl. Takeover) reaches only the
   grantor's *individual* vault — it explicitly cannot read organization
   collections, even ones the grantor owns (verified 2026-06-07,
   [bitwarden.com/help/emergency-access](https://bitwarden.com/help/emergency-access/)).
   Storing these in a Families Collection would silently defeat the nominee
   handoff. (Families is still required — it's what unlocks Emergency Access.)
2. Chandra runs **Bitwarden Families** ($47.88/yr, up to 6 users — *taken
   2026-06-07*) so he can *configure* emergency contacts **and** cover the family
   directly. Each member gets Premium features (so Emergency Access works); the
   nominee can alternatively be a free external Bitwarden account. (Originally
   scoped as individual Premium; upgraded to Families as a deliberate longer-term
   call — see Update below.)
3. Configure the nominee as a **Takeover** emergency contact with a wait time
   (e.g. 2–7 days) so an accidental/early request can still be denied in the
   window.
4. The **private repo holds the runbook** (`docs/decommission.md`) only — it tells
   the nominee *what to do*; Bitwarden gives them the *credentials*.

### Why not the alternatives

- **1Password:** best product, but no managed emergency-access — the nominee path
  is a printed Emergency Kit PDF, which is fragile for an estate scenario and
  pricier with no free tier.
- **Proton Pass:** strong privacy, but emergency access requires a paid plan *and*
  a Proton-address account; Chandra's primary identity is Gmail, so the feature
  wouldn't apply without restructuring his email.
- **KeePassXC:** unbeatable on cost/portability and a good *secondary* offline
  backup, but it has no guided takeover — a non-engineer nominee following
  `decommission.md` is far better served by Bitwarden's managed flow.

### Consequences

- **Positive:** Managed, time-delayed nominee handoff; open-source + self-hostable
  keeps exit cost near zero (tenet 12); modest (~₹330/mo on Families, tenet 6);
  cross-platform (tenet 3); no secret ever touches git.
- **Negative:** One small recurring subscription; nominee must create a (free)
  Bitwarden account and accept the invite ahead of time.
- **Exit:** export the vault to JSON and import elsewhere, or self-host the
  Bitwarden server; no proprietary format lock-in.
- **Secondary backup (optional):** a periodic encrypted KeePassXC `.kdbx` export
  in a safe-deposit/will as a vendor-independent fallback.
- **Operator steps:** see `docs/decommission.md` §0 (set up the vault + emergency
  contact). Rotate any credential that has ever been pasted into a chat/log.

### Update — 2026-06-07: chose Families over individual Premium

Chandra took **Bitwarden Families** ($47.88/yr, 6 users) rather than individual
Premium ($19.80/yr). Rationale: (1) the family password-sharing need (a year of
Gmail/WhatsApp sharing) is real and was always coming — buying it once avoids
paying twice and a later migration; (2) **front-loading an annual cost while the
June paycheck is in hand**, given a possible income change end-June 2026 (financial
context recorded in the private `financial-decisions.md`). The family *rollout*
(onboarding members, migrating passwords) remains a separate task — `BACKLOG.md` P3.

---
