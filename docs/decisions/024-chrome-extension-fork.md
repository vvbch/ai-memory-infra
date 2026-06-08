# ADR 024: Phase 3 — fork mem0's OpenMemory Chrome extension (rewire to our self-hosted server)

**Status:** Accepted — extension will live in its own **private** GitHub repo; repo
setup + cloud-auth → self-hosted `X-API-Key` rewiring are the next implementation steps.
**Date:** 2026-06-08
**Deciders:** Chandra

### Context

Phase 3 (build phases, `AGENTS.md`) is **browser reach**: a Chrome/Chromium extension so
the AI assistants used in a desktop browser (Claude, ChatGPT, Gemini, DeepSeek — tenet-3
cross-platform; ChromeOS is the first-class mobile path per ADR 004) can read from and write
to our self-hosted memory server (`https://memory.chandrav.dev`, Phase 1). ADR 004 already
named the **OpenMemory Chrome extension** as the intended memory-injection mechanism; this
ADR ratifies *which* extension and *how* we adopt it (tenet 12 — a fork is a dependency we
will maintain, so it is deliberated + documented + has an exit).

**Landscape web-verified first (tenet 8; sources = GitHub repos + mem0.ai blog, 2026-06-08):**

- **`mem0ai/mem0-chrome-extension`** ("OpenMemory Chrome Extension") — **MIT**, TypeScript,
  ~670 stars, last push 2026-03. **Archived** ("you're welcome to fork… the MIT license
  still applies"). Ships per-site content scripts for **ChatGPT, Claude, Gemini, DeepSeek,
  Grok, Perplexity** (+Replit) — i.e. all four LLMs in our architecture plus extras. Built
  *for mem0*, so its memory request/response shapes already match a mem0 backend. Coupling to
  mem0's paid cloud is **isolated** to an auth/transport layer: every call hits a hardcoded
  `https://api.mem0.ai/v1/...` with `Authorization: Bearer <google-access_token>` **or**
  `Authorization: Token <api_key>`; there is also PostHog telemetry to `/v1/extension/`.
- **3rd-party forks** (e.g. `Eshaan-Nair/Synq`/ArcRift) — MIT, but each ships its **own**
  full backend (local Ollama models + SQLite/Neo4j/MongoDB/ChromaDB + an MCP server on
  `localhost:3001`) and injects locally-extracted graph context. Adopting one means gutting
  that backend *and* rewriting the inject path to call our server — it duplicates the server
  we built in Phase 1 (against tenet 7).
- **Build from scratch** — a thin Manifest-V3 extension calling our REST API directly.
  Cleanest fit, but we would hand-write and forever maintain all per-site DOM injection
  (the rot-prone part) ourselves.

### Decision

**Fork `mem0ai/mem0-chrome-extension` (MIT) into a separate private GitHub repo and rewire
its transport/auth layer to talk to our self-hosted mem0 server.** Operator chose this over
build-from-scratch and over forking a 3rd-party extension (concierge decision, 2026-06-08).

- **Separate repo, private for now.** The extension is a shippable browser product with a
  different toolchain (Node/TypeScript/Vite), release cadence, Chrome Web Store metadata,
  and privacy-policy surface than this infra repo. It should keep upstream fork history and
  attribution cleanly, not be loose vendored source inside `ai-memory-infra`. It stays
  **private initially** while we do the cleanup/rewrite and license/attribution audit, to
  avoid public confusion while the fork is still raw. We can make it public later once the
  self-hosted rewrite is stable.
- **Keep it a thin REST/MCP client of the live API (tenets 4/7).** The extension stores no
  second brain; it reads/writes our server. VPS down ⇒ the assistants still work (tenet 4).
- **Rewiring scope (next step):** (1) centralize the hardcoded `https://api.mem0.ai` base
  URL (~50 refs across 13 files) into one configurable value → our server; (2) swap the
  `Authorization: Bearer/Token` header for our server's **`X-API-Key`** scheme; (3) replace
  the Google sign-in flow with a simple settings form (server URL + API key + user id);
  (4) **strip the PostHog telemetry** to mem0 (privacy + self-host); (5) verify the
  `/memories` + `/search` request/response shapes against our running server before declaring
  done (tenet 8, tenet 17 — prove it).

### Alternatives considered

- **Build from scratch.** Most control and a perfect thin-client by design, but we eat all
  per-site DOM-injection upkeep. Rejected: Option 1 hands us working, multi-site injection
  for free under MIT.
- **Fork a 3rd-party extension (SYNQ/ArcRift, etc.).** Brings a competing self-hosted
  backend we'd have to gut; new vendor; injects local graph not remote memories. Most effort,
  worst fit (tenet 7). Rejected.
- **Use mem0's hosted cloud + their store-bought extension as-is.** Fastest, but sends our
  memories to mem0's proprietary server (the whole point of Phase 1 was self-hosting) and is
  a lock-in (tenet 12) / tenet-4 hard-dependency. Rejected.

### Consequences (reversible — tenet 12 / 17)

- **Exit path:** it's MIT and isolated in its own repo — archive/delete that repo or remove
  any browser-store listing to back it out. No new paid vendor, no account, no lock-in.
- **We own maintenance.** Upstream is archived, and chat sites change their DOM, so the
  per-site selectors will rot — but that is true of *any* browser-injection extension and is
  exactly the work the fork saves us from writing in the first place. Mitigation: keep the
  per-site config centralized; fix selectors as sites change (a known, bounded chore).
- **No firm IP (tenet 5):** this is public platform code only.
- **Docs/DoD:** `architecture.md` already lists the Chrome extension; `STATUS.md` Phase/Next
  action updated. The infra repo keeps only a pointer under `extension/`; source lives in the
  new private extension repo.

*(Pairs with ADR 004 — ChromeOS as the first-class mobile path for this extension; Android is
best-effort only since Kiwi's Jan-2025 archival.)*
