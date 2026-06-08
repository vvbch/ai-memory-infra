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

## 2026-06-08 — Automating the backups (and a fix to the hand-off itself)

**Focus:** start turning the proven-but-manual backup into something that runs itself,
watches itself, and tells you when it breaks.

**Milestones**
- **The nightly schedule is written.** The server will now back itself up every night at
  midnight (India time) — no human required — and if it happens to be switched off at
  that hour, it runs the missed backup the moment it's back on.
- **A watchdog was chosen and wired in.** After comparing three options, we picked a free,
  open-source monitoring service. The server sends it a quiet "backup OK" ping after each
  run; if that ping ever fails to arrive, the watchdog emails you. This is the only way to
  learn that the *whole machine* died — a dead server can't report its own death.

**Decisions**
- **Pick the lock-in choices in the open.** The one decision that ties you to an outside
  vendor — which watchdog service — was put to the owner with three verified options and a
  recommendation, rather than quietly chosen. Everything reversible (the schedule, the
  wiring) was just built.

**Engineering notes**
- **Build the reversible parts, ask about the one-way doors.** The schedule and the alert
  wiring only *add* behaviour, so they were built directly; the only thing escalated was the
  vendor commitment.
- **A hand-off note should point at the truth, not copy it.** Mid-session we noticed the
  "resume in a fresh chat" note had quietly grown into a full duplicate of the project
  status — costing effort every time and risking drift. We cut it back to a one-line pointer
  ("read the status file, then do the next thing"), because the status file *is* the source
  of truth. Small process leaks compound; fix them when you spot them.

## 2026-06-08 — The nightly backup is now live (and the watchdog is watching)

**Focus:** take the backup automation that was *written* last time and actually switch it
on on the real server — then prove the watchdog sees a real "backup OK".

**Milestones**
- **The server now backs itself up on a schedule.** The nightly job is switched on on the
  live machine; the next run is tonight just after midnight (India time). If the box is ever
  paused, it catches up the missed run when it comes back.
- **The watchdog is confirmed working.** We ran a backup by hand to test the whole chain end
  to end: the backup completed, all the data files landed in the cloud bucket, and the
  monitoring service received the "backup OK" ping and turned green. So from now on, if the
  server ever goes silent at backup time, you'll get an email.

**Engineering notes**
- **Don't trust the live box's state — prove it before changing it.** The server's copy of
  the code had drifted from the saved-to-GitHub version through earlier hands-on sessions.
  Rather than blindly overwrite it, we first compared the two and confirmed the only real
  difference was the new code we *meant* to add — so resetting the server to the GitHub
  version was provably safe and lost nothing.
- **A classic cross-platform paper-cut, caught by testing.** The very first test ping failed
  because copying a setting from a Windows machine to the Linux server left an invisible
  stray character on the end of the line, which broke the web address. Found it, stripped it,
  re-tested, confirmed green. This is exactly why the project insists on Windows *and* Linux
  both working cleanly — and why we test the real path, not just the happy path.
- **Test the scheduled job, not just the script.** We triggered the backup through the same
  scheduler that will run it nightly (rather than running the script directly), so the test
  exercised the exact path that matters.

**What's left for backups**
- Make the backup storage itself resistant to accidental deletion, and set up a recurring
  *practice* restore. Those touch how data could be lost, so they'll be talked through before
  being built — not done silently.

## 2026-06-08 — Making the backups hard to lose (versioning + auto-expiry)

**Focus:** harden *where* the backups live so a mistake — or a compromised server — can't quietly
erase your history. (Talked through first, because anything touching data loss is a one-way door.)

**Milestones**
- **Old versions are now kept, then aged out on a schedule.** The cloud bucket keeps previous
  versions of each backup and automatically expires them on a 30-day / 14-day policy. This runs on
  the storage provider's side, so even a hacked server can't wipe the history — it simply doesn't
  have the power to.
- **The server stopped being allowed to delete backups at all.** The backup job used to prune old
  copies itself; that "delete" ability was removed. Cleanup is now the storage provider's job, not
  the server's.
- **A wrong restore is now recoverable.** Before a restore overwrites anything, the system first
  snapshots the current state — so if you ever restore the wrong thing, you can get back to where
  you were.

**Engineering notes**
- **Don't assume a cloud service can do something just because a famous one can.** We checked the
  provider's actual capabilities first: it supports keeping old versions and auto-expiry, but does
  **not** offer write-once "locked" storage. So the design leaned on what genuinely exists (versioning
  + expiry + removing the server's delete power) instead of a feature that wasn't there.
- **Take power away from the thing most likely to be attacked.** The safest backup is one the
  everyday server *cannot* destroy; moving the cleanup to the storage side does exactly that.

*(House-keeping: this entry and the next were written up one session late — the work shipped on time,
but the public/private journal wasn't updated in the same sitting. Caught and backfilled.)*

## 2026-06-08 — A backup key that can only touch the backups

**Focus:** give the server a **narrow** key that can reach *only* the backup bucket, instead of the
broad key that could touch the whole cloud account.

**Milestones**
- **The server now uses a "backups-only" key.** We created a new access key scoped to just the
  backup bucket, saved it to the password vault, and swapped it onto the server. If that server were
  ever compromised, the key in it can reach the backups and nothing else — no other data, no ability
  to reconfigure the account.
- **Proven before trusting it.** We ran a real backup through the exact nightly path and watched it
  succeed on the new key (all four data files landed in the cloud) *before* retiring the old key's
  use on the server. The broad key was never removed on faith.

**Engineering notes**
- **Verify the new credential works before retiring the old one.** The first test actually *failed* —
  an invisible stray character had corrupted the key during the copy from a Windows machine to the
  Linux server (the same cross-platform paper-cut as before, in a new spot). Because we tested first,
  this surfaced instantly as a clear error instead of becoming a *silent* broken backup discovered
  weeks later. We found the bad byte, repaired it, and re-ran to a clean success.
- **Stop threading text through three layers of shell.** The corruption came from trying to clean the
  value while it passed through three different command interpreters. The durable fix was to do the
  cleaning inside one proper script on the server itself — a recurring lesson, now applied up front.
- **Least privilege brings separation of duties for free.** The narrow key deliberately *can't*
  change the bucket's settings — so the powerful "configure everything" key stays separate and off
  the server entirely, used only from the owner's own machine.

**What's left for backups**
- Set up a recurring *practice* restore (a "drill") so we stay confident the recover-button works.
  That's the last piece before the backup system is considered done.

## 2026-06-08 — A monthly fire drill for restores

**Focus:** the last piece of the backup system — a recurring **practice restore** that proves the
recover-button still works, run safely so it can never harm the live data.

**Milestones**
- **A monthly restore drill, fully automated.** Once a month the server quietly restores the most
  recent backup into a **disposable, throwaway copy** — never the live system — and checks three
  things: that a planted "canary" memory comes back *with its search-vector intact*, that the
  knowledge-graph file reloads cleanly, and that the edit-history file is a valid database. Then it
  deletes the throwaway copy. If a drill ever fails or stops running, a watchdog will email the owner.
- **Proven end-to-end.** We planted the canary, took a fresh backup, and ran the drill for real — it
  **passed**, and afterwards the live system was completely untouched and the throwaway copy was gone.
- **A backup you've never test-restored is only a hope.** This closes that gap: the restore path is
  now exercised on a schedule, so it can't silently rot as the system changes.

**Engineering notes**
- **A drill must never endanger what it's protecting.** The everyday restore tool deliberately
  overwrites the live data, so the drill couldn't reuse it — it needed its own isolated path that
  spins up scratch copies, checks them, and throws them away, with cleanup that runs even if something
  fails midway.
- **Let the real constraint drive the design.** The server is a small machine with no room to run a
  second full copy of everything at once. Rather than fight that, the drill verifies the part that
  actually goes stale — *do the backup files restore into working data?* — which is both safer and
  simpler than cloning the whole system.
- **Make the test deterministic.** The drill checks for a specific, permanently-planted "canary"
  memory, so a pass means something exact ("this known thing came back, search-vector and all"),
  not a vague "looks non-empty."

**What's left for backups**
- One 3-minute setup click for the owner: create a second free watchdog check so a failed or missed
  monthly drill sends an email. After that, the backup system is fully done — every layer scheduled,
  self-monitoring, deletion-resistant, and now drill-tested.

## 2026-06-08 — The backup system is fully closed (drill watchdog is live)

**Focus:** the very last piece — give the monthly restore drill its own watchdog, then verify the
whole thing with a real run. Short concierge session.

**Milestones**
- **The monthly drill now has its own independent watchdog.** We created a second free monitoring
  check (separate from the nightly-backup one), set it to expect a ping on the drill's monthly
  schedule, and wired the server to send it. A passing nightly backup and a passing monthly drill are
  *different* guarantees, so each gets its own alarm.
- **Verified for real, end-to-end.** We ran the drill on the server — it restored the latest backup
  into a throwaway copy, confirmed the canary memory came back with its search-vector, the
  knowledge-graph file reloaded, and the edit-history was valid — then sent its "OK" ping, and the new
  watchdog flipped to **green**. The owner confirmed it on the dashboard.
- **Phase 2 (backup & restore) is now fully closed.** Every layer is scheduled, self-monitoring,
  resistant to accidental deletion, and proven recoverable — with both the nightly backup and the
  monthly drill independently watched. Nothing operator-side remains.

**Engineering notes**
- **Wire the value as a literal on the server side.** Adding the watchdog link to the server's config
  was done as a single self-contained command on the server, sidestepping a recurring
  Windows-to-Linux line-ending gotcha entirely, then verified byte-for-byte that the line landed
  clean.
- **Verify before assuming work is needed.** A standing reminder said the server might need
  re-syncing to the source-of-truth; a one-command check showed it was already in sync, so no
  destructive reset was run. Checking is cheaper than assuming.

**Next**
- **Phase 3 — the Chrome browser extension**, so the memory layer reaches the browser. First step is
  to survey what already exists before building.

## 2026-06-08 — Phase 3 starts: browser extension fork decision

**Focus:** decide the browser-extension path before writing code.

**Milestones**
- **Extension landscape checked first.** We compared mem0's archived MIT Chrome extension, a fresh
  build, and third-party local-memory extensions. The mem0 extension is the best starting point
  because it already has the fragile per-site browser plumbing for ChatGPT, Claude, Gemini,
  DeepSeek, Grok, and Perplexity, while still matching our mem0 server model.
- **Decision captured in ADR 024.** We will fork mem0's extension and rewire it to the self-hosted
  server (`memory.chandrav.dev`) with `X-API-Key`, removing mem0 cloud login and telemetry.
- **Repo boundary corrected before committing.** The extension will live in its own private GitHub
  repo, not inside the infra repo. The infra repo now keeps only the decision record and a pointer.

**Next**
- Create the private extension repo, verify the upstream baseline builds, then do the self-hosted
  auth/URL rewrite there.

## 2026-06-08 — Private extension repo created, baseline build verified

**Focus:** turn the extension-fork decision into a real private repo and prove the raw upstream code
still builds before changing it.

**Milestones**
- **Private repo created.** We created `vvbch/ai-memory-extension` as a private GitHub repo and
  imported the upstream MIT `mem0ai/mem0-chrome-extension` history, preserving attribution while
  keeping the raw fork out of public view during cleanup.
- **Baseline build is green.** After installing normal Node.js tooling on Windows, the raw upstream
  extension passed `npm install` and `npm run build`. That gives us a clean starting point: any future
  breakage comes from our rewrite, not from an unknown imported baseline.
- **Operating rule sharpened.** The docs now say explicitly that routine reversible implementation is
  the agent's job to verify and commit. The owner reviews decisions and outcomes, not every mechanical
  code diff.

**Engineering notes**
- **PowerShell detail:** the machine's bundled Cursor Node did not include npm, so we installed Node.js
  LTS with `winget`. Use `C:\Program Files\nodejs\npm.cmd`; PowerShell blocks the `npm.ps1` shim by
  execution policy.
- **Inherited dependency debt:** npm reported 11 audit findings in the upstream dependency tree. We
  did not run `npm audit fix` blindly before the self-hosted rewrite, because that could change the
  baseline before we understand compatibility.

**Next**
- Rewire the extension in `ai-memory-extension`: server URL to `memory.chandrav.dev`, auth to
  `X-API-Key`, replace mem0 cloud login with local settings, remove telemetry, then verify the REST
  shapes against the live server.

## 2026-06-08 — Extension rewritten for self-hosted Mem0

**Focus:** remove mem0 cloud coupling and make the extension talk to the live self-hosted server.

**Milestones**
- **Cloud auth removed.** The extension no longer scrapes `app.mem0.ai` sessions, asks for Google/mem0
  sign-in, or sends `Authorization: Bearer/Token`. The popup now stores local settings: server URL,
  API key, and user id.
- **Self-hosted API wired.** Memory writes and searches now target the live server shape:
  `https://memory.chandrav.dev`, `X-API-Key`, `/memories`, and `/search`.
- **Telemetry stripped.** The mem0 extension telemetry path is removed/no-op, and the manifest no
  longer grants host permissions to `api.mem0.ai` or `app.mem0.ai`.
- **Build is green.** The rewritten extension passes TypeScript and production build. Code search shows
  no remaining mem0 cloud URLs, PostHog references, or live `Authorization` headers.

**Engineering notes**
- **The live OpenAPI was the source of truth.** We fetched `https://memory.chandrav.dev/openapi.json`
  before changing paths, confirming `/memories`, `/search`, and `X-API-Key`.
- **Lint/format are upstream-noisy.** The imported repo fails `lint:check` / `format:check` on
  Prettier/CRLF issues across many untouched files. We did not reformat the whole fork in the same
  behavioral rewrite.

**Next**
- Load `ai-memory-extension/dist` as an unpacked Chrome extension, enter the real API key from
  Bitwarden, then prove add/search/get from the browser against the running server.

## 2026-06-08 — Chrome unpacked load verified; prompt control-plane tightened

**Focus:** load the rewritten extension in Chrome and fix the stale operator instructions that made
the step harder than it should be.

**Milestones**
- **Unpacked extension loaded.** The operator loaded `ai-memory-extension/dist` in Chrome and confirmed
  **OpenMemory** appears on `chrome://extensions`.
- **Install wording corrected.** The README now follows Chrome's current flow and says to select the
  `dist` folder itself, because it contains `manifest.json`.
- **Control plane tightened.** Agent instructions now require current-doc/live-UI verification before
  giving volatile browser or console click steps, plus an exact target artifact and visible success
  condition.

**Next**
- Enter the real `ADMIN_API_KEY` from Bitwarden in the OpenMemory popup, then prove add/search/get from
  the browser against the running server.
