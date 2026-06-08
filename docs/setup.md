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
(CI runs), merge → CD deploys. That closes Phase 1; Phase 2 is backup/restore.

> **Turning it off again.** Everything you stand up here can be cleanly torn down:
> `docs/decommission.md` covers rollback, pause (stop the bill), and full
> decommission (close every billable account) — `python scripts/teardown.py` does
> the automated part.
