# Setup Guide

Operational walkthrough for standing up the stack. **Phase 1 = provision the VPS
with Terraform and deploy the Compose stack.** Commands that spend money or use
your cloud credentials (`terraform apply`, `ssh`, `doctl`) are marked
**[YOU RUN]** — the agent explains, you execute.

> Resuming? See `docs/planning/STATUS.md` for where we are. Decisions: `docs/decisions/`.

---

## Phase 1 — deploy to the VPS

### What you'll have at the end
A 4GB droplet in Bangalore running Mem0 + Postgres/pgvector + Neo4j + dashboard
behind Caddy with HTTPS on `memory.`, `dash.`, `graph.` (+ `monitor.` reserved),
all provisioned by Terraform.

### Prerequisites (one-time accounts & secrets)

You need these before Step 1:

1. **DigitalOcean API token** — cloud.digitalocean.com → API → *Generate New
   Token* (read+write). Provisions the droplet, firewall, and Spaces bucket.
2. **Cloudflare API token** — dash.cloudflare.com → My Profile → *API Tokens* →
   *Create Token* → use the **Edit zone DNS** template scoped to your domain
   (ADR 016). Needed for Terraform to create A records.
3. **DO Spaces keys** — API → *Spaces Keys* → generate. A separate access-id +
   secret pair (NOT the API token) for the backups bucket and remote state.
4. **SSH keypair** — `ssh-keygen -t ed25519 -C "ai-memory-infra"`. Terraform
   uploads the *public* key; the private key is how you SSH in.
5. **Domain registered at Cloudflare** — buy `chandrav.dev` (or your chosen name)
   at Cloudflare Registrar *before* `terraform apply`. This creates the DNS zone
   Terraform writes records into. See Step 0b below.
6. **An OpenAI API key** — platform.openai.com. Serves both extraction
   (`gpt-5-mini`) and embeddings (`text-embedding-3-small`). **The project must
   allow *both* models** (or "Allow all models"): if the project is scoped to
   only `gpt-5-mini`, `text-embedding-3-small` returns 403 and every `add`
   silently fails. The per-model allow-list UI has been flaky — prefer
   *Project → Limits → Allow all models*. (Cost stays capped by auto-recharge
   OFF + the org budget; tenet 15.)

---

### Step 0b — register the domain at Cloudflare  **[YOU RUN, one-time]**

> **ELI5:** Buy the web address at Cloudflare. That automatically creates the
> "phone book" Terraform will fill in when the server exists.

1. Log in at **dash.cloudflare.com** (create a free account if needed).
2. Left sidebar → **Domain Registration** → **Register Domains**.
3. Search **`chandrav.dev`** → add to cart → complete checkout (~$10–12/yr
   at-cost). Cloudflare assigns its nameservers automatically — **no delegation
   step** (unlike the old ADR 012 flow).
4. Confirm the domain appears under **Websites** with status *Active*.

> **Deeper:** Registrar lock applies for 60 days before you can transfer out
> (tenet 12 exit cost). DNS propagation is usually minutes once Terraform creates
> the A records in Step 3.

---

### Step 0 — fill in your variables

> **ELI5:** Copy the two example files to real ones and paste your secrets in.
> The real files are gitignored so they never get committed.

```powershell
cd infra\terraform
copy terraform.tfvars.example terraform.tfvars   # then edit: do_token, cloudflare_api_token, spaces keys, ssh_public_key, domain_name, backup_bucket_name
cd ..
copy .env.example .env                            # then edit: secrets + OPENAI_API_KEY + DOMAIN/ACME_EMAIL
```

> **Deeper:** Generate the `.env` secrets with:
> `openssl rand -base64 48` (JWT_SECRET), `openssl rand -base64 32` (ADMIN_API_KEY),
> `openssl rand -base64 24` (POSTGRES_PASSWORD, NEO4J_PASSWORD), and
> `docker run --rm caddy:2-alpine caddy hash-password` (BASIC_AUTH_HASH). Set
> `DOMAIN` in `.env` equal to `domain_name` in `terraform.tfvars`.

---

### Step 1 — initialize Terraform

> **ELI5:** Download the plugins Terraform needs (DigitalOcean + Cloudflare).
> Safe, no changes.

```powershell
cd infra
make tf-init          # or: terraform -chdir=terraform init
make tf-fmt           # formatting check (optional but nice)
```

> **Deeper:** `init` reads `main.tf`'s `required_providers` and pulls
> `digitalocean/digitalocean ~> 2.0` and `cloudflare/cloudflare ~> 5.0` into
> `.terraform/`. State is local for now (`backend.tf` is commented until the
> Spaces bucket exists — see Step 5).

---

### Step 2 — preview the plan

> **ELI5:** Terraform shows you exactly what it *would* create. Nothing happens
> yet. Read it like a receipt before paying.

```powershell
make tf-plan          # or: terraform -chdir=terraform plan
```

> **Deeper:** Expect ~9 resources to add: 1 ssh key, 1 droplet, 1 firewall,
> 4 Cloudflare A records (memory/dash/graph/monitor) + 1 apex, 1 Spaces bucket,
> plus a zone data read. Confirm region `blr1`, size `s-2vcpu-4gb`, and that
> `domain_name` matches your Cloudflare-registered domain. If the plan shows
> anything you didn't expect, stop.

---

### Step 3 — apply (creates real, billable infra)  **[YOU RUN]**

> **ELI5:** This actually builds the droplet and DNS records. It starts the
> ~₹2,000/mo meter. Run it yourself; type `yes` when prompted.

```powershell
make tf-apply         # or: terraform -chdir=terraform apply
```

> **Deeper:** Uses your `do_token`. Takes ~1 min. On success it prints outputs.
> If it fails midway, `terraform apply` is idempotent — fix the cause and re-run;
> it only creates what's missing.

---

### Step 4 — read the outputs

```powershell
terraform -chdir=terraform output
```

> You need `droplet_ipv4` (SSH target). DNS A records are created automatically
> at Cloudflare — no nameserver step.

---

### Step 5 — (optional) move Terraform state to Spaces

> **ELI5:** Right now your state file is on your laptop. This puts it in the cloud
> bucket so it's not laptop-only.

Create a small state bucket, uncomment the block in `backend.tf`, set the
matching `endpoints` region, then:

```powershell
$env:AWS_ACCESS_KEY_ID="<spaces_access_id>"; $env:AWS_SECRET_ACCESS_KEY="<spaces_secret_key>"
terraform -chdir=terraform init -migrate-state
```

> **Deeper:** DO Spaces is S3-compatible; Terraform's `s3` backend works with the
> `skip_*` flags already in `backend.tf`. Credentials come from the env vars
> above, never the file.

---

### Step 6 — bootstrap the droplet  **[YOU RUN]**

> **ELI5:** SSH into the new server, get the code, paste your `.env`, run one
> script that installs Docker and starts everything.

```bash
ssh root@<droplet_ipv4>
git clone <your-repo-url> /opt/ai-memory-infra
cd /opt/ai-memory-infra/infra
cp .env.example .env && nano .env        # paste the SAME secrets as local (prod DOMAIN/URLs)
sudo bash ../scripts/bootstrap.sh
```

> **Deeper:** `bootstrap.sh` installs Docker + Compose + git, sets UFW
> (22/80/443), then **builds the Mem0 API image from source** and brings the
> stack up (`docker compose … up -d`), polling the API. The build is automatic
> and reproducible: it clones the pinned mem0 source (`MEM0_REF` in the script)
> and runs `docker build -f infra/mem0-server.Dockerfile -t mem0-api-server:local
> <src>/server`. We build because the published `mem0/mem0-api-server` image is
> arm64-only (no amd64) and omits the Neo4j graph deps; the Dockerfile adds those
> plus the gpt-5-mini extraction patch (ADR 021) and carries a build-time `assert`
> that fails loudly if a future mem0 ref breaks the patch. The `compose pull` step
> pulls only the external images (caddy/postgres/neo4j) — the local Mem0 image
> isn't pulled, and the dashboard is profiled-off (P2). In prod `.env`, set
> `DASHBOARD_URL=https://dash.<domain>` and `DASHBOARD_API_URL=https://memory.<domain>`
> so CORS + the (later) dashboard work. To bump the mem0 version, override
> `MEM0_REF=<git-sha>` when running the script.

---

### Step 7 — health check

```bash
curl -fsS https://memory.<domain>/docs >/dev/null && echo OK
```

Then in a browser: `https://dash.<domain>` (dashboard, basic-auth),
`https://graph.<domain>` (Neo4j Browser, basic-auth). `monitor.` activates in
Phase 8.

> **Deeper:** First TLS handshake may take a few seconds while Caddy fetches
> Let's Encrypt certs. If you get cert errors, confirm DNS resolves to the droplet
> (`nslookup memory.<domain>`). Logs:
> `docker compose -f docker-compose.yml -f docker-compose.prod.yml logs mem0 --tail 50`.
> If a `POST /memories` returns `200` but stores **0 memories**, extraction failed
> silently — almost always the OpenAI project model-access (see Prereq 6: allow
> both `gpt-5-mini` and `text-embedding-3-small`).

---

### Done when
API answers over HTTPS, dashboard + Neo4j Browser load behind basic auth, and a
test `POST /memories` round-trips. Then update `STATUS.md`, commit, open the PR
(CI runs), merge → CD deploys. That closes Phase 1.

> **Turning it off again.** Everything you stand up here can be cleanly torn down:
> `docs/decommission.md` covers rollback, pause (stop the bill), and full
> decommission (close every billable account) — `python scripts/teardown.py` does
> the automated part.

---

## Phase 2 — backups (`scripts/backup.sh` / `scripts/restore.sh`)

### What this gives you
Off-box copies of all three datastores in the Spaces bucket, and a proven way to
get them back. Design + trade-offs: **ADR 022**.

### One-time prerequisite — Spaces creds in the droplet `.env`
The scripts read the bucket + Spaces keys from `infra/.env`. Add these (the same
Spaces pair as `terraform.tfvars`; see `.env.example`) — **never** commit them:

```bash
BACKUP_BUCKET=ai-memory-infra-backups-chandrav
SPACES_REGION=sgp1
SPACES_ACCESS_KEY=...      # DO console → API → Spaces Keys
SPACES_SECRET_KEY=...
```

### Take a backup  **[on the droplet]**
```bash
sudo bash /opt/ai-memory-infra/scripts/backup.sh
```
> **Deeper:** installs `s3cmd` on first run, then: `pg_dump -Fc` (Postgres,
> online) + `tar` of the mem0 SQLite history (online) + an **offline** Neo4j dump
> (briefly stops/starts neo4j — Community Edition can't dump a running DB; only
> the graph pauses ~20–30 s, the API stays up). Uploads all three + a SHA-256
> `MANIFEST.txt` to `s3://$BACKUP_BUCKET/backups/<UTC-timestamp>/`. **The script no
> longer deletes anything** — retention is enforced **server-side** by a Spaces
> lifecycle rule (ADR 023 §3: current backups expire after 30 days; a deleted/
> overwritten copy stays recoverable 14 more days via bucket *versioning*). Backups
> also run **automatically** nightly via a `systemd` timer (00:00 IST), monitored by
> a dead-man's-switch (ADR 023 §1–§2); the command above is the manual/on-demand path.

### Restore  **[on the droplet — DESTRUCTIVE]**
```bash
sudo bash /opt/ai-memory-infra/scripts/restore.sh            # newest backup
sudo bash /opt/ai-memory-infra/scripts/restore.sh 20260608T062241Z   # a specific one
```
> **Deeper:** downloads the prefix, **verifies checksums against the manifest**,
> then asks you to type `RESTORE` (set `FORCE=1` to skip for automation). It first
> takes a **pre-restore safety snapshot** of the *current* state (so a wrong restore
> is itself recoverable — set `SKIP_PRESNAPSHOT=1` only if the current state is
> already broken/unbackupable), then stops mem0, `pg_restore --clean`s Postgres,
> wipes+untars the SQLite volume, and does an offline Neo4j `load --overwrite`,
> before bringing everything back. Give Neo4j ~30 s to warm up, then verify with a
> `/search`.

### Restore DRILL  **[on the droplet — SAFE; never touches live data]**
A monthly "fire drill" that proves the restore path still works, by restoring the
latest backup into **throwaway scratch containers** and asserting a known canary
survived. Runs automatically via a `systemd` timer (1st of the month, 01:00 IST);
the commands below are the manual/setup path. Design: **ADR 023 §4**.

```bash
# One-time: plant the permanent canary memory the drill checks for, then take a
# fresh backup so it's included.
sudo bash /opt/ai-memory-infra/scripts/plant-drill-canary.sh
sudo systemctl start ai-memory-backup.service

# Run a drill on demand (the timer also runs it monthly):
sudo bash /opt/ai-memory-infra/scripts/restore-drill.sh
```
> **Deeper:** the drill verifies the SHA-256 manifest, restores `postgres.dump`
> into a scratch `pgvector` container and asserts the canary row exists *with a
> non-null embedding*, `neo4j-admin load`s the graph dump into a throwaway volume
> (a clean load proves restorability), and checks the mem0 history tar is a valid
> SQLite file — then tears all scratch down. It **never** touches the live
> Postgres/Neo4j/mem0 volumes. Lightweight (no full second stack) because the 4 GB
> box has no headroom for one. To alert on a failed/missed drill, create a *second*
> healthchecks.io check and set `DRILL_HEALTHCHECK_URL` in the droplet `.env` (see
> `.env.example`).

### Done when
`backup.sh` lands four files in the bucket, a restore round-trips a known memory
(verified 2026-06-08, ADR 022), and the monthly restore **drill** passes against a
throwaway target (verified 2026-06-08, ADR 023 §4). That closes Phase 2; Phase 3 is
the Chrome extension fork.

## Phase 4 — MCP clients

The deployed Mem0 server currently exposes REST (`/memories`, `/search`) but not
an MCP endpoint. Phase 4 therefore starts with a local stdio MCP proxy
(`ai-memory-mcp`) that calls the live REST API with `X-API-Key` (ADR 025).

### Local environment

Set these on the machine that starts the MCP client:

```powershell
$env:AI_MEMORY_BASE_URL = "https://memory.chandrav.dev"
$env:AI_MEMORY_USER_ID = "chandrav"
$env:AI_MEMORY_API_KEY = "<from Bitwarden: ai-memory-infra ADMIN_API_KEY>"
```

Do not commit the key. `AI_MEMORY_BASE_URL` and `AI_MEMORY_USER_ID` have those
defaults in code; only `AI_MEMORY_API_KEY` is required.

### Cursor / VS Code MCP config

Use a stdio server that runs the installed entrypoint:

```json
{
  "mcpServers": {
    "ai-memory": {
      "type": "stdio",
      "command": "ai-memory-mcp",
      "env": {
        "AI_MEMORY_BASE_URL": "https://memory.chandrav.dev",
        "AI_MEMORY_USER_ID": "chandrav",
        "AI_MEMORY_API_KEY": "${env:AI_MEMORY_API_KEY}"
      }
    }
  }
}
```

### Claude Code

The parent workspace has a checked-in `.mcp.json` for Claude Code. After
`AI_MEMORY_API_KEY` is set in the shell that launches Claude Code, open Claude
Code from the parent `ai-memory` workspace and approve the project MCP server if
prompted.

If adding manually:

```powershell
claude mcp add ai-memory -- ai-memory-mcp
```

### Done when

At least one MCP client lists `search_memories`, `add_memory`, and `list_memories`,
then successfully searches for a known live memory without pasting the API key in
chat. Claude mobile/iOS uses the remote HTTP endpoint below instead of a local
stdio process.

### Remote MCP connector for Claude (incl. iPhone) — ADR 034

The droplet serves the same three tools over Streamable HTTP at
`https://mcp.chandrav.dev/` (Caddy → `mcp-proxy` container), gated by a dedicated
bearer token (`MCP_CONNECTOR_BEARER_TOKEN` in the droplet `infra/.env`; master
copy in Bitwarden — not the admin API key).

Register it once on the web (mobile inherits connectors from web/desktop):

1. Open `claude.ai` → **Settings** → **Connectors** → **Add custom connector**.
2. Name: `ai-memory`. URL: `https://mcp.chandrav.dev/`.
3. In the advanced/auth field, paste the bearer token from Bitwarden
   (`MCP_CONNECTOR_BEARER_TOKEN`).
4. Save, then enable the connector in a chat (search-and-tools menu). On the
   iPhone Claude app it appears after the web registration syncs.

Verify: ask Claude to search memories for a known live fact; writes land with
`metadata.source=mcp`. Token rotation = regenerate, update droplet `.env`,
`docker compose up -d mcp-proxy`, re-paste in the connector settings.

## IDE startup/handoff hooks (session bootstrap + completion gate)

Two lifecycle hooks make sessions cheaper and safer (ADR 030 + ADR 027). Both are
**editor-agnostic Python in `scripts/`** — no logic lives in any `.cursor/`
directory (tenet 2):

- `scripts/session_bootstrap.py` — on session start, injects a compact block
  (control plane = `ai-memory-infra`, current phase, the Next action from
  `STATUS.md`) so a fresh agent doesn't re-read all of `AGENTS.md`/`STATUS.md` to
  resume (token cost, tenet 16).
- `scripts/completion_gate.py` — on turn end, blocks a stop while any project repo
  is dirty/unpushed and forces the commit/push DoD for any model.

### Install (one-time per machine / after any re-clone)

Each IDE loads *project* hooks from the **open workspace root** — here the parent
`ai-memory` workspace, which is not a git repo. So a versioned installer generates
the thin per-IDE adapters there (same model as the git-hook installer, ADR 015):

```powershell
python ai-memory-infra/scripts/install_ide_hooks.py
```

This writes one thin adapter per harness at the parent workspace root, each a
pointer that just runs the `scripts/` logic with the flag matching that harness's
hook contract (verified, tenet 8):

| Harness | Adapter file | SessionStart | Turn-end gate |
| --- | --- | --- | --- |
| Cursor | `.cursor/hooks.json` | `--cursor` (`additional_context`+`env`) | `stop` → `followup_message`, `loop_limit 4` |
| Claude Code | `.claude/settings.json` | plain text (stdout = context) | `Stop` → `followup_message` |
| Codex CLI | `.codex/hooks.json` | `--hookspecific` (`hookSpecificOutput.additionalContext`) | `Stop` → `--decision` (`decision: block`) |
| Gemini CLI | `.gemini/settings.json` | `--hookspecific` | none — Gemini's `SessionEnd` is advisory-only (no blocking per-turn stop) |
| Grok | `.grok/settings.json` | `--hookspecific` | `Stop` → `--decision` (best-effort; see note) |

The same two `scripts/` files back every adapter (no per-IDE logic, no drift —
tenet 10); they expose one output mode per contract. **Re-run after any
re-clone** — the generated files live at the unversioned parent root and don't
survive on their own (the installer + the `scripts/` logic are what's versioned).

> **Grok note.** The Grok CLI ecosystem is fragmented across several incompatible
> config schemas (xAI *Grok Build* `.grok/hooks.json` + `~/.grok/config.toml`,
> `grok-dev` `~/.grok/user-settings.json`, `superagent-ai/grok-cli`
> `.grok/settings.json`). The installer writes the common nested Claude-style
> `.grok/settings.json`; confirm with `grok inspect` / `/hooks` and adjust the
> builder in `install_ide_hooks.py` if your CLI reads a different file/shape.

### Verify

- **Cursor:** reloads `hooks.json` on save (else restart). Check **Settings →
  Hooks** / the **Hooks** output channel; on a fresh chat the bootstrap block
  should appear. Note: Cursor's `sessionStart` `additional_context` injection has a
  known timing bug that can drop it — the script also exports `env` pointers and
  prints to the Hooks channel, and the structural token win (Next-action excerpt vs
  whole `STATUS.md`) holds regardless.
- **Claude Code:** `.claude/settings.json` `SessionStart`/`Stop` run the same
  scripts.
- **Codex CLI:** project `.codex/` hooks load only once **trusted** — run `/hooks`
  to review + trust them (and confirm `[features] hooks` isn't disabled in
  `config.toml`; it's on by default). `SessionStart` injects the bootstrap as
  developer context; `Stop` blocks the turn with `decision: block` until repos are
  clean (it allows the stop after one nudge — Codex sets `stop_hook_active`).
- **Gemini CLI:** open the `/hooks` panel; `SessionStart` injects the bootstrap.
  Gemini has **no blocking per-turn stop** (its `SessionEnd` is advisory-only), so
  only the bootstrap is wired — the completion gate is enforced on the other
  harnesses.
- **Grok:** run `grok inspect` (or `/hooks`) to confirm the adapter was discovered;
  if not, your Grok CLI uses a different schema — see the Grok note above.
- **VS Code:** no native agent session hook. Wire the bootstrap as a folder-open
  task instead — run `python ai-memory-infra/scripts/session_bootstrap.py` (plain
  text mode) and read its output, or add it to `.vscode/tasks.json` as a
  `folderOpen` `runOptions` task. Same canonical script, no duplicated logic.

### Done when

`python ai-memory-infra/scripts/session_bootstrap.py` prints the bootstrap block
(and `--hookspecific` emits the `hookSpecificOutput.additionalContext` JSON), the
five adapters exist at the workspace root, and a `{"status":"completed"}` piped
into `scripts/completion_gate.py` reports any dirty/unpushed repo — as
`followup_message` by default and as `{"decision":"block",…}` with `--decision`.
