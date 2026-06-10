# Build Journey — how this was built (public summary)

> A curated, session-by-session summary of how this infrastructure was built —
> milestones, key decisions, and rough effort. Distilled from a detailed private
> build log; **decisions** live in `docs/decisions/` (ADRs), the **current state**
> in `docs/planning/STATUS.md`, and the **how-to** in `docs/setup.md`.
>
> Append-only. Personal/operational detail is deliberately omitted.

---

## 2026-06-10 — Standards pay rent: ChatGPT and Perplexity get designed in for near-zero new code

**Focus:** with Claude's remote connector live, the operator pointed at the next
two platforms — ChatGPT and Perplexity. The morning's post-mortem lesson applied
directly: before designing anything, verify what each platform's **own** docs say
about user-added remote MCP connectors. This session was research + the decision
record; registration comes next.

**Milestones**
- **First-party verification, both platforms.** OpenAI's developer docs: custom
  remote MCP servers are supported as apps, and "developer mode" (Plus plan and
  above, web registration) gives a full read/write MCP client over OAuth — with
  dynamic client registration supported and static tokens explicitly not.
  Perplexity's help center and changelog: custom remote connectors shipped
  March 2026 (Pro plan and above), OAuth 2.0 with dynamic client registration,
  Streamable HTTP transport. Third-party setup guides were read but deliberately
  marked non-load-bearing.
- **The OAuth bet pays off.** Both platforms speak exactly the protocol surface
  already deployed for Claude: OAuth 2.1 + dynamic client registration + PKCE
  over Streamable HTTP. The new ADR's expected server change is one cosmetic
  edit — the consent page stops saying "Claude" and names whichever client is
  asking. One server, one secret class, three platforms.
- **Honesty gates kept.** The architecture coverage table only changes after a
  live memory round-trip on each platform; mobile availability is treated as
  unverified until seen working; and the plan-tier requirements (paid tiers on
  both platforms) are surfaced as an explicit operator spend decision, not
  assumed.

**Effort:** ~40 minutes, agent-side research and documentation.

**Next**
- Confirm the operator's plan tiers, generalize the consent-page copy, then
  concierge the two registrations with live verification — Perplexity first.

---

## 2026-06-10 — Remote MCP, take two: self-hosted OAuth because the client demands it

**Focus:** the remote memory endpoint for Claude on iPhone was deployed and
verified earlier today behind a static bearer token — and then the registration
screen revealed that claude.ai custom connectors accept **only OAuth** (or no
auth at all). No field to paste a token into. This session turned that
dead-end into a working OAuth 2.1 authorization server without adding a single
new dependency or vendor.

**Milestones**
- **A blameless post-mortem first.** The miss was documented as a correction-of-
  errors record: the design had been verified against the API-path connector
  docs, not the consumer UI's own auth page. The systemic fix — when a design's
  viability depends on a third-party surface the agent can't exercise itself,
  that surface's own documentation gets verified at design time — is now part
  of the decision record (ADR 035, superseding the auth section of ADR 034).
- **Own the policy, not the protocol.** The MCP SDK already pinned in the
  project ships the entire OAuth protocol surface: discovery metadata, dynamic
  client registration, PKCE S256 verification, the token endpoint. The new code
  is one module of single-user policy: a consent page where the operator pastes
  the existing connector secret to approve a client, opaque rotated tokens
  (access 1 h / refresh 60 d) stored SHA-256-hashed in a small state file on a
  Docker volume — so connector sessions survive redeploys and the file never
  contains a usable secret. The old static token still works for curl-style
  verification, so nothing about the operational runbook breaks.
- **Tested like it matters.** Twenty-five new tests drive the exact flow Claude
  performs — registration → authorize → consent → PKCE token exchange →
  authorized tool call — plus the abuse paths: wrong consent password, tampered
  PKCE verifier, replayed authorization codes, expired and garbage tokens.
  Suite: 103 passed, 94% coverage, strict typing clean.
- **Rehearsed live before involving a human.** After deploy, the agent ran the
  full OAuth dance end-to-end against the public endpoint itself — discovery,
  registration, consent approval, token exchange, and a memory search with the
  issued token returning real memories. The only steps left for the operator
  are the two that genuinely require human hands: saving the secret to the
  password vault and clicking through claude.ai's connect flow.

**Next**
- Operator registration on claude.ai (an OAuth connect + one consent-page
  approval), confirmation on the iPhone app, then the day's third goal: a
  memory-bank snapshot and an honest knowledge-graph status report.

---

## 2026-06-10 — Memory Daily Driver v0, Phase 2: talking to your memory bank

**Focus:** wire the Phase 1 verbs into normal conversation, so "plan my day" or
"log this and remind me Friday" just works — and answer three product questions
with evidence: when does this work with Claude, how does past context get in,
and what happens when a decision is reversed later?

**Milestones**
- **The conversational practice shipped.** The agent's canonical instructions now
  map natural phrases to the daily-driver verbs: planning requests render the
  agenda (overdue first, one recommended next action); "log / remind / follow up"
  phrases capture open items with resolved dates; recruiter reachouts are tagged
  to the career category automatically; decisions are captured verbatim with
  their reasons; "done" closes an item with *what actually happened*. Every write
  is followed by a confirmation of exactly what was stored — a silent write is
  defined as a contract violation, so mislabels are catchable in the same breath.
- **Decision reversals get a supersession flow.** A reversed decision is never
  edited away: the agent records a *new* decision naming what it supersedes and
  why. The trail is the history; the latest entry is the current truth — and
  because every surface (editor agent, ChatGPT via the extension, Claude) writes
  to the same single bank, this holds across tools and sessions. Underneath, the
  memory service also keeps its own change-log of every add/edit/delete with
  before-and-after values (verified from the deployed version's source).
- **Proven live, safely.** Read-only agenda ran green against the real bank; a
  full capture → plan → recruiter board → close → delete round-trip ran under a
  throwaway account, leaving the real bank untouched.
- **An honest discovery, parked deliberately.** While verifying the history
  story from source, we found the deployed open-source memory service ships *no*
  knowledge-graph writing code — the graph database is running and backed up but
  receives nothing from the memory layer today (the install flag that looked
  like it enabled graph support is a silent no-op in this version). Our
  architecture docs overstated this; a top-priority backlog item now tracks
  verifying the live graph is indeed empty and correcting the docs, rather than
  derailing this session's goal.

**Next**
- The premise test (Phase 3): put real open items and a couple of real recruiter
  follow-ups in, run "plan my day" for a few days, and judge whether the memory
  layer genuinely earns its keep. Then a short decision record consolidating the
  v0 choices.

---

## 2026-06-09 — Memory Daily Driver v0, Phase 1: the helper that the daily features sit on

**Focus:** with the read/write foundation proven (Phase 0), build the thin tool
layer that captures and retrieves to-dos, decisions, and recruiter follow-ups —
with the right labels enforced automatically — so the conversational features
have something safe to call.

**Milestones**
- **Taught the shared API client three new tricks.** It can now store text
  *verbatim* (for authored to-dos) or let the service summarize it (for raw
  notes); filter searches on structured fields server-side; and fetch, update, or
  delete a single item by id. The "update in place" path was verified against the
  memory service's published update contract before relying on it.
- **Built the daily-driver helper.** A small, dependency-light tool with plain
  verbs: log an open item / a decision / a fact; *plan the day* (it sorts open
  items into overdue, due today, needs-a-follow-up, and upcoming — sorted by date
  on the client so it works regardless of server-side date filtering); show the
  recruiter board (open items tagged as career); and close an item with a note of
  *what actually happened*, which updates it in place so its id and original
  creation time are preserved.
- **Made the labelling non-optional.** Every write goes in under the single
  identity with a mandatory source tag and a validated kind/status/category and
  ISO dates — bad input is rejected before it can reach the bank, so the memory
  stays queryable and consistent.
- **Verified two ways.** A unit-test suite (client + helper, using a mock
  transport) plus type and lint gates all pass; then the whole flow was exercised
  *live* against the real service under a throwaway test account — capture, plan,
  recruiter board, close, confirm the closure stuck with all fields intact, delete
  — leaving the real bank untouched.

**Next**
- Wire these verbs into normal conversation (Phase 2): saying "plan my day" or
  "log this and remind me Friday" should just work, with the agent confirming what
  it stored. Then a real-use test, then a short decision record capturing the v0
  choices.

---

## 2026-06-09 — Memory Daily Driver v0, Phase 0: proving the memory layer is usable

**Focus:** before writing any product code, prove that an agent can actually
read from and write to the live memory service, and that a hand-authored "open
item" (a todo with a due date and a follow-up date) survives the round-trip with
all of its structure intact.

**Why this first:** the whole point of the Daily Driver is to *use* the memory
layer conversationally (plan the day, track recruiter follow-ups). That premise
is worthless if the agent can't reliably talk to the service, so this session was
pure de-risking — no feature code.

**What was proven (all against the live service, over plain REST):**
- The agent can authenticate and read the memory bank.
- Writing a todo *verbatim* works — the service stores the exact words instead of
  running them through its AI summarizer, which is what you want for an authored
  to-do item.
- Every structured field on the todo (its kind, its status, its due date, its
  follow-up date, its category tags, and where it came from) comes back intact on
  both a direct read and a search — and the service auto-stamps when it was
  created.
- Search can filter on those fields on the server side, so "show me only the open
  recruiter items" won't require pulling everything down and sifting locally.
- Deleting a todo works, so the full lifecycle is reachable.

**Outcome:** the read/write foundation is solid. The probe ran against throwaway
test data that was deleted afterward, leaving the real bank untouched. Next step
is the thin helper layer that the conversational features will sit on.

---

## 2026-06-09 — Built a concierge guardrail for operator handoffs

**Focus:** stop the agent from ever handing a human a vague or overstuffed
instruction, by turning the "concierge mode" rule into a mechanism.

**Milestones**
- **Shipped the Operator Assistant concierge action formatter.** A small,
  editor-agnostic command that takes any step the agent must delegate to a person
  and renders it in one fixed shape: a plain-English reason, the exact single
  thing to do, what success looks like, and a "tell me what you see" pause.
- **Made vague and multi-step instructions fail loudly.** A `--check` mode refuses
  to pass when a part is missing, when the wording is hand-wavy ("confirm it",
  "make sure", "do the needful"), or when the "one action" is really several steps
  chained with "then" or a numbered list — so a sloppy delegation can't reach the
  operator.
- **Kept secrets out by design.** The instruction may *point at* where a credential
  lives (a password-vault folder) but can never contain the secret itself.
- **Verified live.** A valid action rendered cleanly; the check correctly caught
  vague, missing, and multi-step inputs; lint clean.

**Decision**
- The recurring "be a good concierge" rule is now enforced by a tool, not trusted
  to memory — the same move already applied to repo handoffs.

## 2026-06-09 — Built the first agent-owned skill: a session checkpoint

**Focus:** turn "write a good handoff at the end of each step" from a hope into a
mechanism, as the first skill owned by a defined agent persona.

**Milestones**
- **Shipped the Build Agent session-checkpoint skill.** A small, editor-agnostic
  command that reads the real git state of every project repo (which branch, any
  uncommitted changes, anything unpushed, the latest commit) and turns it into a
  ready-to-paste checkpoint — without dumping a long chat transcript.
- **Made the handoff contract checkable.** A `--check` mode passes only when every
  touched repo is committed and pushed and the essential fields (what was done, how
  it was verified, what's next) are present — so a "done" claim can't quietly skip a
  repo. It's the *capture* partner to the existing turn-end *trigger* gate.
- **Kept facts and judgment separate.** The tool owns the verifiable facts (git
  state, formatting, validation); the agent still writes the human summary. It never
  auto-overwrites the prose status file and never touches secrets.
- **Verified live.** The check correctly caught an in-progress repo; the render and
  machine-readable output were clean; lint clean.

**Decision**
- Skills are owned mechanisms, not loose commands: each declares its owning persona,
  what it may store, and a visible success condition before it's built.

## 2026-06-09 — Verified the "commit before you stop" safety net actually works

**Focus:** prove the deterministic completion gate is genuinely live, after a prior
session ended with unsaved work despite the gate existing.

**Milestones**
- **Found the real failure mode: a not-yet-active safety net.** The gate was correctly
  installed at the workspace root, but the editor's hooks screen showed it as *configured*
  with **zero execution history** — it had never actually run. The prior miss happened
  because the gate was built one session and trusted the next, before anyone confirmed it
  was firing.
- **Confirmed it fires and enforces.** Ending a real turn recorded the stop hook; a
  reversible self-test (drop a throwaway file, run the gate, delete it) proved it **blocks**
  when work is uncommitted and **allows** when everything is clean and pushed.
- **Turned the lesson into a mechanism.** The hook installer now prints a "verify it
  actually fires — configured is not firing" reminder, so the next install is checked for a
  real execution, not just a parsed config file.
- **No new incident report needed.** This was an instance of an existing lesson ("a control
  you can't show firing is not a control"), so the one new takeaway was folded into the
  existing record rather than duplicated.

**Decision**
- A safety control is only trustworthy once you've *watched it fire* — listing it as
  configured proves nothing. Make that verification a standing step, not a one-time hope.

## 2026-06-09 — Made the IDE hooks portable + added a session bootstrap

**Focus:** stop coupling automation to one editor, and stop burning tokens
re-discovering the project layout every session.

**Milestones**
- **Found a latent defect.** The deterministic completion gate from the prior
  session had been placed in a per-editor directory that the open workspace root
  never loads — so the "guarantee" was likely inert, and it coupled the project to
  one IDE against the portability tenet.
- **Established a portable hook pattern.** Canonical, editor-agnostic logic lives in
  plain scripts; each IDE gets a thin, generated adapter at the workspace root
  (Cursor and Claude Code today; VS Code documented as a folder-open task). This is
  the same "thin pointer + versioned installer" shape already used for editor rules
  and git hooks.
- **Added a session bootstrap.** A startup hook now injects a compact block — where
  the control plane is, the current phase, and the single next action — so a fresh
  session doesn't re-read large context files just to get oriented.
- **Verified live.** Both hooks fire from the real workspace root; the startup
  context injection has a known editor-side timing bug, so the script also falls
  back to environment pointers and a log-channel print.

**Decisions**
- Lifecycle hooks are portable infrastructure, not editor features: logic in shared
  scripts, per-IDE adapters generated by a versioned installer, re-run on re-clone.
- A corrective action must be checked against the rest of the principles and
  verified actually running — a fix that breaks portability or never loads is a new
  problem, not a closed one.

## 2026-06-09 — Closed the agent/persona pre-build gate

**Focus:** define the agents that will own future memory skills before building
the skills themselves.

**Milestones**
- **Added `docs/agent-personas.md`.** The first three personas are Build Agent,
  Research and Strategy Agent, and Operator Assistant, with Memory Steward as a
  supporting hygiene role.
- **Used the recent COEs as design input.** The first skills are ordered around
  the actual failure modes: session checkpointing, all-repo handoff verification,
  and concierge formatting for operator actions.
- **Moved the backlog forward.** The pre-build gate is marked done; the next
  work is implementation of the first agent-owned skills.

**Decision**
- Skills must declare an owner persona, allowed store/retrieve behavior, never-store
  boundaries, visible success condition, and canonical repo/doc before they are built.

## 2026-06-09 — Tightened COE and concierge handoff controls

**Focus:** close a repeat governance failure before continuing the MCP client check.

**Milestones**
- **Verified the local MCP handoff state.** Repo-health was green, the required
  environment variable was already present without printing its value, and the local
  `ai-memory-mcp` command was on PATH. Current Cursor guidance places MCP servers under
  `Settings → Tools & MCP` (older builds may use `Features → Model Context Protocol`).
- **Opened a repeat-failure COE.** The agent had added cognitive load by asking for a vague
  "confirm it" check and had printed a resume prompt before checkpointing repo state.
- **Upgraded the COE standard.** The template and existing COEs now include an industry
  benchmark section comparing the response against AWS/Amazon COE and Google SRE
  blameless-postmortem practices.

**Decisions**
- **Resume prompts are checkpoint-gated.** A fresh-session prompt is valid only when
  `STATUS.md` and required logs are current at a logical handoff point, and not while the
  assistant is waiting on an operator action in the same flow.
- **Operator-delegated steps now use a fixed concierge format:** purpose, exact UI path or
  command, visible success condition, and a wait point.
- **The final all-repo handoff verifier is now P1**, not P2, because repeated human-caught
  handoff failures show that prose gates are insufficient.
- **Cursor MCP visibility is proven.** After reload, Cursor listed a workspace MCP server named
  `ai-memory`.
- **Next work is a pre-build product gate.** Before any more build work, define the agents/personas
  that will use the memory layer; skills/tools come after those definitions.

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

## 2026-06-08 — Sidebar Recent Memories fetch fixed

**Focus:** handle the first browser-side failure after saving the API key.

**Milestones**
- **Failure observed.** After saving the API key, the OpenMemory sidebar showed **Error loading
  memories** in Recent Memories.
- **Sidebar API path corrected.** The sidebar now uses the shared self-hosted API helpers for
  `serverUrl`, `apiKey`, and `userId`, handles non-2xx responses explicitly, and accepts the
  self-hosted memory list response shape.
- **Build is green.** `npm run type-check` and `npm run build` pass after the fix.

**Next**
- Reload the unpacked extension in Chrome, reopen OpenMemory, then continue browser add/search/get
  verification.

## 2026-06-08 — Browser reload still shows extension runtime errors

**Focus:** stop the session at a clean debug boundary.

**Milestones**
- **Reload tested.** The unpacked extension was reloaded after the sidebar fetch fix.
- **Errors captured.** On `https://chatgpt.com/`, Chrome still reports `Error fetching memories:
  TypeError: Failed to fetch` from the sidebar bundle, plus `Cannot create item with duplicate id
  mem0.saveSelection`.

**Next**
- In a fresh session, inspect the extension runtime/service-worker/content-script errors, verify whether
  the fetch failure is CORS/host-permission/request-context related, make context-menu registration
  idempotent, rebuild, reload, and continue browser verification.

## 2026-06-08 — ChatGPT sidebar loads live memories after reload

**Focus:** prove the rebuilt extension works in the real Chrome profile after the background-relay fix.

**Milestones**
- **Repo health is green.** The control-plane and private repos both passed the standard health check and
  were `0 ahead / 0 behind` remote.
- **Real Chrome extension reloaded.** OpenMemory was reloaded from the installed unpacked `dist` folder,
  not a separate test profile.
- **ChatGPT sidebar is green.** On `https://chatgpt.com/`, the OpenMemory sidebar opened and loaded live
  Recent Memories: **Total Memories = 1**, with a memory card plus Copy/View actions. The prior visible
  `TypeError: Failed to fetch` sidebar failure did not recur.

**Next**
- Prove ChatGPT-side save/search behavior against the live server, then close the Phase 3 browser-reach
  milestone if that path is green.

## 2026-06-08 — Handoff gate sharpened

**Focus:** fix the process miss where completed session work was checkpointed locally but not committed
and pushed.

**Milestones**
- **Miss caught immediately.** The sidebar verification work was done, but the session handoff was
  incomplete because the docs were left only in the local working tree.
- **Control plane clarified.** The project instructions now state that continuing the next action from
  `AGENTS.md`/`STATUS.md` is standing authorization to commit and push reversible completed work.
- **Handoff model reaffirmed.** GitHub, not a local working tree, is the atomic session boundary for the
  next agent.

**Next**
- Continue Phase 3 with ChatGPT-side save/search verification, and commit+push every touched repo before
  ending the session.

## 2026-06-08 — Package repo handoff fixed; COE opened

**Focus:** close the second handoff miss: the extension package itself had not been pushed.

**Milestones**
- **Extension repo pushed.** `ai-memory-extension` had local commits and uncommitted background-relay
  source changes. The package now passes `type-check` and `build`, and the relay fix is pushed as
  `97530f8`.
- **COE opened.** `docs/coe/2026-06-08-atomic-handoff-failure.md` records the repeated atomic-handoff
  failure, impact, detection gap, 5-whys, and corrective actions.
- **Control plane sharpened again.** Completion now explicitly means every touched repo: control plane,
  private logs, and package repos. A P2 final all-repo handoff verifier is parked.

**Next**
- Continue Phase 3 with ChatGPT-side save/search verification. Final response must report the latest
  pushed commit for every repo touched in that session.

## 2026-06-08 — Proved ChatGPT OpenMemory save/search

**Focus:** prove the browser extension's ChatGPT path against the live self-hosted server.

**Milestones**
- **Automatic ChatGPT save is proven.** A fresh verification codeword was absent from live search, then
  a normal ChatGPT prompt asking to remember it caused the live server to store a new memory for the
  extension user.
- **Live search is proven.** A semantic `/search` for the matching question returned three memories,
  including the exact codeword memory.
- **Visible plugin retrieval is proven.** The OpenMemory sidebar in the real Chrome profile showed
  **Total Memories = 3** and displayed the newly saved codeword memory in Recent Memories.

**Decision**
- **Parked the inline composer modal as polish.** The ChatGPT composer icon is present, but the inline
  dark modal opens off-screen or mostly invisible in the current layout. This does not block the product
  goal: memory capture and retrieval are already seamless without manual modal clicks. The issue is
  tracked for a later extension polish pass.

**Next**
- Move to MCP client reach: connect Claude and Cursor/VS Code as thin clients of the same live memory
  server.

## 2026-06-08 — Built and proved local MCP reach

**Focus:** connect developer-tool MCP clients to the live self-hosted memory server.

**Milestones**
- **Fixed the workspace control-plane gap.** Added parent-workspace pointers so future agents immediately
  know `ai-memory-infra` is the control plane.
- **Found the real MCP shape.** The live server exposes `/memories` and `/search`, but no `/mcp` routes;
  direct probes returned 404.
- **Built the first MCP bridge.** Added `ai-memory-mcp`, a local stdio MCP proxy that exposes
  `add_memory`, `list_memories`, and `search_memories` while storing all data in the live REST API.
- **Configured clients without secrets in git.** Added Cursor, VS Code, and Claude Code project configs
  that read `AI_MEMORY_API_KEY` from the local environment.
- **Verified live MCP search.** A Python MCP client listed the tools and found the Phase 3 codeword through
  `search_memories` against `https://memory.chandrav.dev`.

**Next**
- Set the persistent `AI_MEMORY_API_KEY` user environment variable from Bitwarden, reload Cursor, and
  confirm the `ai-memory` MCP server appears.

## 2026-06-09 — Corrected MCP handoff

**Focus:** fix the handoff process after verified Phase 4 work was left local.

**Milestones**
- **Opened a COE.** Captured the missed commit/push and missing fresh-session prompt as a control-plane
  failure, not a one-off typo.
- **Tightened the final gate.** `AGENTS.md` now blocks final responses unless touched git repos are pushed
  or blockers are named, and the answer includes a copy-paste resume prompt.

**Next**
- Commit/push the corrected control-plane and private-log changes, then continue from a fresh session.

## 2026-06-09 — Made the commit/push gate deterministic

**Focus:** stop relying on the model to remember to commit and push.

**Milestones**
- **Diagnosed a wrong-layer problem.** Switching models (GPT-5.5, high reasoning) ended a session
  with work unpushed. The "commit and push every session" rule lived as prose the model had to
  choose to follow, so adherence varied by model — confirmed as a known agent behavior, not a
  config bug.
- **Researched the industry pattern.** Agent harnesses converge on a `stop` lifecycle hook for this:
  hooks are deterministic because the *harness* runs them, while rules and skills are run by the
  model and so vary. Git hooks only validate a commit already happening — they can't start one.
- **Shipped a harness-level completion gate.** Added a Cursor `stop` hook that checks every project
  repo when a turn ends and, if anything is uncommitted or unpushed, forces the agent to finish the
  full Definition of Done (commit, push, update status), and raises a loud operator-facing alert if
  it still can't after a few tries. It enforces the process rather than blindly auto-committing, so
  documentation and good commit messages are preserved.
- **Closed a long-standing item.** This is the "repo handoff verifier" promised across several prior
  corrections, now implemented as a mechanism instead of a reminder.

**Next**
- Resume the first agent-owned skill (Build Agent session checkpoint), with the handoff verifier
  already in place.

---

## 2026-06-09 — A decision is a contract, not a document (ADR 031)

**Milestones**
- **Caught a cross-repo blind spot.** A settled rule — every memory uses one identity (`chandrav`)
  and is tagged by a `source` that must reach both stores — had been written and committed in the
  control-plane repo but never applied to the browser extension or the local API proxy, the clients
  that actually write memories. So most browser-captured memories were landing under the wrong
  identity with their source tag silently dropped.
- **Named the real bug as a pattern, not an instance.** The project's automated gates enforce a
  repo's git *hygiene* (everything committed and pushed, no secrets) but nothing checked that a
  cross-cutting decision was actually *true* in every repo it governs. A clean control-plane repo
  was hiding a sibling that quietly violated the decision.
- **Fixed both layers.** Routed every extension write through a single normalizing path (correct
  identity + source in metadata, with old values auto-healed) and corrected the proxy default; then
  closed the systemic gap with a new decision record (a cross-cutting decision is a *contract* that
  must hold in every consumer repo), a Definition-of-Done row, and a small conformance check script
  that fails if a client drifts — so this is caught by a machine next time, not by a person noticing.

**Next**
- A post-deploy probe to confirm a browser-written memory shows the right source tag in both the
  search results and the knowledge graph, under the single identity.

---

## 2026-06-10 — Documents are code too; the repo gets a standing maintenance crew

**Milestones**
- **Caught a planning file silently decaying into a log.** The project's "read this first to
  resume" file is meant to be a snapshot, overwritten each session — but across ~20 sessions it had
  quietly grown 9x by accumulating old updates, duplicating the real journal. The root cause was
  systemic: code contracts had machine validators (lint, types, secret scans), document contracts
  were policed by prose and good intentions. Wrote it up blamelessly, trimmed the file (history was
  already safe in the journal and git), and shipped a test-driven shape validator that now runs
  before every commit and in CI — so this class of drift can't land again.
- **Continuous integration went from claimed to real.** Lint, types, tests, and both contract
  gates now run on every push and pull request; a lint failure had in fact been sitting on main
  with nothing to catch it.
- **The repo gained a standing maintenance crew, deliberately not tied to any IDE.** Orchestration
  is plain GitHub Actions with the agent prompts versioned in the repo: when CI fails, an agent
  investigates and opens a fix PR within minutes; every Saturday morning a scan agent reviews the
  whole repo — redundancies, inconsistencies, tests, and an architecture benchmark against industry
  standards — and files a report plus a PR of safe fixes. Hard guardrails are structural: the
  runners hold zero live credentials, everything lands as a reviewable PR, and irreversible changes
  are recommended but never applied.
- **A one-word session resume.** The canonical resume prompt is now a `/resume` slash command,
  generated per-IDE by the same versioned installer that manages the lifecycle hooks.

**Next**
- One-time setup of the two automation secrets, then back to the product: the Memory Daily Driver
  premise test.

---

## 2026-06-10 — Making the build model-agnostic: structure over prose

**Focus:** a deliberate control-plane hardening pass before resuming product work,
prompted by a real observation — switching the underlying model (a strong
high-reasoning model vs. a faster, cheaper one) changed how faithfully the agent
followed the project's tenets, guidelines, and operating style. The root cause: the
operating contract was ~900 lines of prose the model had to read and choose to honor.
The fix direction: structured, enforced inputs instead of freeform text.

**Milestones**
- **Secrets are now catalogued, not just stored.** A private secrets catalog lists
  every credential the system uses — its purpose, where the real value lives (the
  console to rotate it / the password-manager item), how to rotate it, and the blast
  radius if it leaked — all without ever recording a value. The password manager stays
  the single home for values; the catalog is the single index. Creating or rotating a
  secret is now "not done" until it is in both.
- **The architecture docs were made honest.** A source review found the docs claimed a
  live knowledge graph that the deployed memory service does not actually populate. The
  graph database is running and backed up, but reserved for a later phase, not written
  today. Every place that overstated this was corrected and the decision recorded, with
  the engineering practices relabeled to separate what is live from what is still a
  target — and four empty, failing placeholder CI workflows were removed.
- **Design discipline became a mechanism.** New work now starts with a short design doc
  (high- and low-level design: components, interfaces, data contracts, failure modes,
  test plan) before code, and the system's cross-component contracts are catalogued in
  one registry that marks how strongly each is enforced.
- **A model-agnostic contract, designed.** The chosen direction: turn the operating
  contract into a structured single source that both renders the human-readable docs
  and drives the automated gates, plus a coverage report that makes visible which rules
  are deterministically enforced versus prose-only — so the model-dependent surface can
  be measured and shrunk over time. The build itself is scoped as the next focused
  session.

**Next**
- Implement the structured operating contract, or run the product premise test — both
  are queued; the order is the operator's call.

---

## 2026-06-10 — Rotated the admin password the clean way, and made the secret index trustworthy

**Focus:** close the last control-plane hygiene item — neutralise a partially-exposed
admin password by rotating it — and make the index of secrets accurate.

**Milestones**
- **The leaked-prefix risk is gone.** The admin-UI password (a fragment of which had once
  slipped into a private file's history) was rotated to a fresh, stronger hash, the new
  value stored in the password manager, the proxy reloaded, and the new login verified live
  (correct password accepted; no/old password rejected). The old fragment is now a dead
  credential — fixed by rotation, with no history rewrite needed.
- **The secret index now names names.** Prompted by a sharp operator question, every entry
  in the secrets catalog was mapped to the exact password-manager item that holds its value
  (several were unnamed or ambiguous, and the admin password had no dedicated item at all).
  A latent mix-up between two storage keys — a least-privilege backup-only key and the
  broader infrastructure key — was corrected at the same time.
- **Plaintext swept off the box.** A convenience block that had kept the admin password in
  plaintext inside the server's environment file (deliberately retained through the live
  burn-in week) was deleted now that the value is safely in the vault — with the live
  configuration confirmed intact and the on-disk backups removed.
- **A documentation claim, confirmed against the live system.** The graph database was
  queried directly and holds zero nodes — matching the earlier source-based finding that the
  deployed memory service writes nothing to it yet.
- **Routine maintenance, made deliberate.** Security patches were waiting on a reboot; the
  box was rebooted (the stack self-recovers) and a standing monthly patch-and-reboot practice
  was written down so this stops drifting.

**Next**
- Implement the structured operating contract (the model-agnostic upgrade), then run the
  product premise test.

---

## 2026-06-10 — The operating contract becomes structured (model-agnostic)

**Focus:** stop the project's operating contract from being ~900 lines of prose that a
model has to *read and choose* to follow — because adherence visibly varied when switching
between a strong model and a cheaper/faster one. Make the high-value rules structured data
backed by mechanisms, and let the human-readable prose be *generated* from that source.

**Milestones**
- **One structured source of truth for the contract.** The 18 tenets, the engineering
  practices, and the Definition-of-Done trigger table now live as machine-readable records,
  each carrying the rule verbatim plus an honest enforcement status — *enforced* (a gate
  fails on violation), *tested*, or *prose* (relies on the agent honoring it).
- **The prose is now generated, and can't drift.** A renderer regenerates the relevant
  sections of the canonical instructions and the tenets document from that source, and
  writes a coverage report. A check runs in pre-commit and CI: edit the prose without
  editing the source and the commit fails. The migration was proven faithful by showing the
  regenerated text is byte-for-byte identical to the previous hand-written prose — the only
  change was inserting the generation markers.
- **The model-dependent surface is now measured.** The coverage report tallies 38 rules:
  11 are enforced by deterministic gates, the other 27 are still prose. That number is the
  thing to shrink over time, deliberately, instead of hoping.
- **First rule promoted from prose to enforced.** A new check makes the editor "pointer"
  files (which should only say "read the canonical instructions") fail the build if they
  ever start copying real rules into themselves — closing a previously hand-caught drift.

**Effort:** about half a session, almost entirely agent-side (design, code, tests, docs),
with no console or operator steps required.

**Next**
- Run the product premise test (live, conversational), or keep hardening by converting the
  next highest-value prose rule into a gate.

## 2026-06-10 - Hardening for a model switch: discoverable skills + a handoff verifier

**Focus:** the next sessions move to a different coding model, so the operating
contract must not depend on any one model's diligence. Two gaps closed: the agent
skills existed as specs + scripts but were not *discoverable* by the editor's
skill system, and the "is this handoff actually clean?" check was still partly manual.

**Milestones**
- **Skills are now auto-discovered by the editor.** The three persona skills
  (memory daily driver, session checkpoint, operator-action formatter) ship as thin
  versioned trigger files that the existing installer copies to where the editor
  looks for them - same generated-adapter model as the session hooks. Placement was
  verified against current editor docs first: nested skill folders are scoped to
  their directory's files, so conversational skills must install at the workspace
  root.
- **A final handoff verifier (test-driven, 7 tests).** One command now answers
  "is every repo clean, pushed, and in sync - and was the status snapshot the last
  thing committed?" It also prints the latest pushed commit per repo, so a session's
  closing claims cite git evidence instead of asserting cleanliness. The turn-end
  gate remains the deterministic floor; this adds stale-clone detection and
  checkpoint-freshness on top.
- This closes the promoted P1 governance backlog item that three separate handoff
  post-mortems had been pointing at.

## 2026-06-10 - The fourth surface: a remote MCP endpoint goes live

**Focus:** the one memory surface that couldn't work yet was Claude on iPhone — a phone
app can't launch a local helper process, it needs a public HTTPS endpoint speaking the
MCP protocol. The design (a dedicated subdomain, a dedicated bearer token rather than
reusing the admin key, OAuth deferred as the multi-user path) was decided in an ADR the
session before; this session built and shipped it.

**Milestones**
- **Same tools, new transport.** The remote endpoint reuses the exact tool code the local
  editor proxy already runs — search, add, list — so there is one implementation and one
  write contract, not a fork. The new code is a thin HTTP shell: an auth gate plus the
  protocol library's built-in HTTP transport, test-driven (six tests, written first).
- **Defense kept proportionate.** Requests without the dedicated token get a 401; the
  transport's DNS-rebinding protection stays on, scoped to the subdomain; the container
  talks to the memory API over the internal Docker network so the admin key never leaves
  the server. Token rotation is a two-minute operation by design.
- **Shipped end-to-end in one session:** DNS record via Terraform (the plan showed
  exactly one resource to add), a small container behind the existing reverse proxy, and
  a live verification from the public internet — unauthorized requests rejected,
  an authorized MCP search returning real memories.
- **Cost: zero new spend** — the container rides the existing box.

**Effort:** ~45 minutes, almost entirely agent-side. The only human steps left are
account-bound by nature: saving the token in the password vault and registering the
connector in the Claude account settings.

**Next**
- Operator registers the connector (web first; mobile inherits it), confirms an iPhone
  round-trip — then the day's third goal: a memory-bank snapshot + an honest graph report.

## 2026-06-10 — ChatGPT joins the same remote MCP server (ADR 036)

**Focus:** close the last ADR 036 web surface — ChatGPT developer-mode custom app on the
existing `mcp.chandrav.dev` OAuth endpoint (same server as Claude and Perplexity).

**Milestones**
- **OAuth connected** after a consent-page fix: ChatGPT's popup stalled on a bare HTTP
  302; an HTML auto-redirect + manual fallback link unblocked the callback.
- **Live-verified read path:** proxy logs show `CallToolRequest` → Mem0 `/search` 200
  when the operator enabled ai-memory per-chat and forced `search_memories` (ChatGPT's
  UI shows abbreviated snippets, not full JSON — logs are the honest proof).
- **Coverage matrix + setup** updated with ChatGPT operator lessons (per-chat toggle,
  explicit tool prompts, don't trust vague "search my memories" or Google namespaces).
- **COE** for session-end "want me to commit?" — standing authorization means commit+push
  is routine, not a second ask.

**Next**
- Mobile inherit spot-checks (Perplexity + ChatGPT apps); then BACKLOG (Goal 3 or hardening).

## 2026-06-10 — ADR 036 closed on iPhone (all three platforms)

**Focus:** operator spot-check that Perplexity, ChatGPT, and Claude mobile apps
inherit the web-registered ai-memory connector and can call it.

**Milestones**
- **Perplexity iPhone:** ai-memory connector visible and live (inherited from web).
- **ChatGPT iPhone:** ai-memory connector visible and live (inherited from web).
- **Claude iPhone:** Load all connectors enabled; operator query triggered a real
  connector call.
- **Coverage matrix + STATUS** updated — ADR 036 is complete on every targeted surface.

**Next**
- Goal 3: memory-bank snapshot + honest knowledge-graph status report (ADR 032).

## 2026-06-10 — Goal 3: honest memory-bank snapshot

**Focus:** count what's actually in production — vector memories and graph nodes —
without overstating capabilities.

**Findings**
- **56 Mem0 memories** (2026-06-08 → 2026-06-10); 47 from the Chrome extension;
  only 3/56 carry explicit `source` metadata (ADR 028 debt).
- **Neo4j node count = 0** — no knowledge graph written today (ADR 032).

**Next**
- ADR 028: enforce `source` on writes; OpenClaw adapter gate before enabling writes.

## 2026-06-11 — ADR 028 Neo4j source propagation probe

**Focus:** BACKLOG P2 top item — does `metadata.source` reach Neo4j when Mem0 writes?

**Findings**
- **pgvector ✅** — live probe: `metadata.source="neo4j-probe"` round-trips on `GET /memories/{id}`.
- **Neo4j N/A today** — `node_count=0` before and after the tagged write; Mem0 ships no graph store (ADR 032). Graph-side `source` moves to LifeGraph Phase 6, not a Mem0 patch.

**Shipped**
- `scripts/verify_source_propagation.py` + tests for repeatable live checks.

**Next**
- MCP droplet redeploy so ADR 037 delete/update tools are live in production.
