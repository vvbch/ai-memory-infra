# Build Journey — how this was built (public summary)

> A curated, session-by-session summary of how this infrastructure was built —
> milestones, key decisions, and rough effort. Distilled from a detailed private
> build log; **decisions** live in `docs/decisions/` (ADRs), the **current state**
> in `docs/planning/STATUS.md`, and the **how-to** in `docs/setup.md`.
>
> Append-only. Personal/operational detail is deliberately omitted.

---

## 2026-06-08 — Made "no secrets in git" a machine-enforced gate

**Focus:** turn the project's "never commit secrets" rule from prose into an automatic,
deterministic check. Short, single-task session (concierge mode).

**Milestones**
- **Added a secret-scanning pre-commit gate.** Every commit now runs a scanner (gitleaks)
  over the staged changes; if it spots anything that looks like a key, token, or password,
  the commit is **blocked before it can reach the remote**. This sits alongside the existing
  repo-integrity check as a second gate in the same hook.
- **Made the gate reliable, not optional.** The hook *blocks* if the scanner isn't installed
  (a security check that silently does nothing is worse than one that asks to be set up), and
  the install script now ensures the scanner is present, so the protection survives a fresh
  clone.
- **Proved it works both ways.** A planted fake credential was caught and the commit stopped;
  a clean change set passed cleanly.

**Decisions**
- **Reused the existing hook + the scanner's native binary** instead of adopting a separate
  hook framework — fewer moving parts, and it slots into the install path already in place. The
  scanner's rules are pinned in a versioned config that extends the maintained default ruleset.
- **Added a "burn-in before hardening" principle.** When something first goes live it's
  reasonable to keep a few convenience affordances for the first week of real use, then remove
  them in a deliberate cleanup pass — *provided* the deferral is explicit, tracked, and
  time-boxed, and never covers an active risk. One leftover cleanup item was consciously parked
  under this rule (safe to hold, because the new gate would block it from git anyway).

**Engineering notes**
- Verified the tool's current usage before wiring it in (the recommended command had changed in
  a recent major version), then confirmed the exact flag against the installed binary.
- Tested the hook by running it directly rather than through a real commit, to exercise the gate
  without creating throwaway history.

## 2026-06-08 — Made the deployment reproducible (close Phase 1)

**Focus:** turn a deploy that needed a manual, by-hand image build into one a single script
reproduces from scratch. Short, single-task session (concierge mode).

**Milestones**
- **Re-baked the application image from its blueprint and proved the fix is permanent.** A
  prior session had hand-patched a bug *inside the running container* (a scratch-layer fix that
  a rebuild would discard). This session rebuilt the image from the corrected blueprint, then
  deliberately destroyed-and-recreated the container — the exact operation that used to revert
  the fix — and re-ran the memory round-trip: a fact was extracted, stored, retrieved, and
  found by search. The fix now lives in the image, not on a sticky note.
- **Folded the from-source build into the install script.** The installer now clones a
  *pinned* revision of the upstream source and builds the image automatically, and only
  downloads the third-party base images (it no longer chokes trying to "download" an image that
  only exists locally). A clean reinstall now works end-to-end.
- **Updated the setup guide** to match: the build is automatic, and a new prerequisite note
  spells out the external provider's model-access requirement that silently broke the first
  round-trip.

**Decisions**
- **Pinned the upstream source to an exact revision** (overridable) so the build is
  deterministic, backed by a build-time self-check that fails loudly if a future upstream
  version moves the code the patch depends on.
- **Build on the server rather than publish to a registry** — fewer moving parts and no extra
  account/secret to manage for a single-node deploy; revisit only if it ever goes multi-node.

**Engineering notes**
- Treated the running, healthy stack as precious: rebuilt the image (which doesn't touch the
  live container), verified the fix was baked in via a throwaway container, and only then swapped
  the live one — each step reversible.
- Verified at three levels — the image source, the recreated container's code, and a real
  end-to-end round-trip — rather than trusting any single signal.
- The production secret never left the server: the authenticated test ran on the host, reading
  the key from the environment, never into logs or chat.

## 2026-06-08 — Verified the running models; isolated a provider-side block

**Focus:** confirm the live server actually uses the chosen models, then prove a memory
round-trips end to end. Short, single-task session (concierge mode).

**Milestones**
- **Model configuration verified against the *running* server**, not just the config file:
  the deployed service genuinely loads the intended small extraction model and the intended
  embeddings model at start-up. Corrected a stale planning note that wrongly assumed those
  settings were ignored — they're read at boot, with a cheaper model as the silent fallback if
  the variable is ever unset (so it must stay pinned).
- **Round-trip test blocked by an external provider setting, cleanly root-caused.** The API
  login itself worked; saving a memory failed because the LLM provider **project was scoped to
  a single model** and refused the embeddings model every save needs. Verified by calling the
  provider directly (extraction model → success; embeddings model → *project has no access*),
  which isolated the fault to provider configuration rather than our stack or key.

**Decisions**
- **Locked the deployment's auth approach as a formal decision record** (built-in admin key,
  never the upstream "bootstrap" helper that would duplicate the database stack) so it isn't
  re-litigated in future sessions.
- **Removed an over-tight model allow-list in favour of the real cost guardrail.** The hard
  spend cap is the prepaid budget with auto-recharge off — not a per-project model list — so
  the list was loosened to unblock embeddings without weakening cost control.

**Engineering notes**
- A vague upstream "authentication" error actually meant a *model-permission* denial; only
  bypassing the memory layer and hitting the provider API directly revealed the true cause.
- Distinguished a provider's **model-list** view from its **inference authorization**: a model
  can appear available yet still be refused at call time (a known, current provider dashboard
  bug). Trusted the live call as ground truth and stopped after a few evidence-based retries
  rather than waiting indefinitely.
- Kept the production secret on the server throughout — the authenticated test runs on the
  host, reading the key from its environment, so it never crosses into logs or chat.

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

## 2026-06-08 — First memory stored end-to-end (round-trip working)

**Focus:** prove the deployed memory API actually stores and retrieves a memory —
the functional milestone that makes the stack *usable*, not just *up*.

**Milestones**
- **Round-trip verified:** writing a message to the API now extracts structured
  facts, persists them, and returns them on a later read and a semantic search.
- Cleared **two stacked blockers** behind one symptom: a model-provider
  permission setting, then a library bug — neither visible without reading the
  service logs and testing the provider directly.

**Decisions**
- **ADR 021** — patched the memory library's model-family detection so the chosen
  extraction model is sent only the parameters it accepts (the newer model family
  rejects an older token-limit parameter the library still sent). Kept the chosen
  model; this is an upstream-bug compatibility patch, not a model change. The fix is
  in the image build with a **build-time assertion** so a future library upgrade
  fails loudly instead of silently reverting the workaround.

**Engineering notes**
- **A `200 OK` can be a silent failure** — the API returned success while storing
  zero memories because fact-extraction threw and was swallowed. Lesson: assert on
  the *effect* (the fact comes back on read/search), never on the status code; the
  service logs were the only place the real error surfaced.
- **Tool-fit over brute force** — debugging through nested shells corrupted both a
  secret header and the diagnostic output; switching to a small script that reads
  secrets from the process environment (no shell expansion) removed a whole class of
  quoting bugs.
- **Reversible-first** — proved the fix on the running service (a throwaway,
  restart-surviving in-place patch) *before* committing to the durable image rebuild,
  keeping a clean revert path the whole way.

## 2026-06-08 — Backups that we actually proved we can restore

**Focus:** make the data survivable — back up all three datastores off-box, and
*prove* a restore brings a real memory back (not just assume it would).

**Milestones**
- **Backup pipeline live:** one command snapshots the memory database, the
  knowledge graph, and the edit-history file into cloud object storage under a
  timestamped folder with checksums, keeping the most recent few.
- **Restore proven, not assumed:** saved a known memory (a codeword), backed up,
  **deleted** it, ran the restore, and the exact memory came back — and a semantic
  search found it again, confirming the embeddings (not just the rows) restored.
- One destructive command, two safety rails: it verifies checksums against the
  backup's manifest and requires a typed confirmation before overwriting anything.

**Decisions**
- **ADR 022 — backup/restore design.** Each store gets the method that's
  consistent with the least downtime: the relational DB and the edit-log are copied
  live; the graph DB's free edition can only be dumped while stopped, so the script
  briefly pauses just the graph (~20–30 s) while the rest of the service stays up.
  Picked the smallest standard tool that does the job over heavier alternatives
  (fewer moving parts), and reused the server's existing secret store for the
  storage credentials rather than inventing a new one.

**Engineering notes**
- **Run it for real.** Two failures only showed up on the live box, not in a syntax
  check: a read-only mount tripped the database image's startup ownership step, and a
  database literally named "neo4j" made a "rename" become a no-op that aborted the run.
  Both were one-line fixes — but only visible by actually executing the path.
- **Prove restores destructively but safely.** Take the snapshot first, delete only
  the known test record, restore, verify the *exact* record and a search result, then
  clean up. A backup you've never restored is a hope, not a backup.
- **Secrets via files, never the command line.** Moving the storage keys onto the
  server went through a temporary file that was shredded afterward; only key *lengths*
  were ever printed.

## 2026-06-08 — A backup review that changed a rule, not just the code

**Focus:** before building more, stop and ask *how good are these backups, really?* —
and let the answer reshape both a principle and the plan.

**Milestones**
- **Strategy reviewed in the open:** named the two numbers that decide every backup
  design — how much data you can lose (we were weak: backups ran *by hand*) and how
  fast you recover (we were strong: one command, minutes). Plus the honest gaps: a
  failed backup told no one, and the backups themselves weren't protected from
  accidental or malicious deletion.
- **A principle got sharper, not just the system.** We caught that destructive actions
  (overwrite-on-restore, delete-on-cleanup) had been treated as routine because the
  *code* was easy to undo — even though the *data loss* wouldn't be. The rule now says:
  judge a decision by whether its **effect** can be undone, not its code. Ask before
  building anything that can erase or overwrite data.
- **Backups, properly automated, became part of the job.** Automatic daily backups, an
  alarm when one fails, delete-resistant storage, a safety snapshot taken *before* any
  restore, and a regular practice-restore are now in scope — not a "maybe later".

**Decisions**
- **Run it in, then close it out.** Rather than declare backups "done" while they still
  needed a human to remember them, we reopened the phase and wrote the automation plan
  down — including leaving one genuine choice (which monitoring service to trust) to the
  owner instead of quietly picking it.

**Engineering notes**
- **A dead machine can't email you that it's dead.** The right way to be told a backup
  stopped is an outside watcher that expects a regular "I'm alive" ping and raises the
  alarm on silence — not the server trying to report its own failure.
- **Don't bake a vendor capability you haven't checked.** We declined to assume the
  object store supports versioning/immutability just because similar services do — it's
  a thing to verify before relying on it.
- **The cheapest, highest-leverage change was a sentence in the rulebook.** No code
  shipped; the lasting output was a tightened principle that prevents a whole class of
  "oops, that deleted data" mistakes.
