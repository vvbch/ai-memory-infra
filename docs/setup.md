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
   Token* (read+write). This is what Terraform uses to create the droplet/DNS.
2. **DO Spaces keys** — API → *Spaces Keys* → generate. A separate access-id +
   secret pair (NOT the API token) for the backups bucket and remote state.
3. **SSH keypair** — `ssh-keygen -t ed25519 -C "ai-memory-infra"`. Terraform
   uploads the *public* key; the private key is how you SSH in.
4. **A registered domain** — buy a cheap name at any registrar. The name is still
   TBD on our side; you'll put it in `terraform.tfvars`.
5. **An OpenAI API key** — platform.openai.com. Serves both extraction
   (`gpt-4.1-nano`) and embeddings (`text-embedding-3-small`).

---

### Step 0 — fill in your variables

> **ELI5:** Copy the two example files to real ones and paste your secrets in.
> The real files are gitignored so they never get committed.

```powershell
cd infra\terraform
copy terraform.tfvars.example terraform.tfvars   # then edit: do_token, spaces keys, ssh_public_key, domain_name, backup_bucket_name
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

> **ELI5:** Download the DigitalOcean plugin Terraform needs. Safe, no changes.

```powershell
cd infra
make tf-init          # or: terraform -chdir=terraform init
make tf-fmt           # formatting check (optional but nice)
```

> **Deeper:** `init` reads `main.tf`'s `required_providers` and pulls
> `digitalocean/digitalocean ~> 2.0` into `.terraform/`. State is local for now
> (`backend.tf` is commented until the Spaces bucket exists — see Step 6).

---

### Step 2 — preview the plan

> **ELI5:** Terraform shows you exactly what it *would* create. Nothing happens
> yet. Read it like a receipt before paying.

```powershell
make tf-plan          # or: terraform -chdir=terraform plan
```

> **Deeper:** Expect ~9 resources to add: 1 ssh key, 1 droplet, 1 firewall, 1 DNS
> domain (zone), 4 A records (memory/dash/graph/monitor) + 1 apex, 1 Spaces
> bucket. Confirm region `blr1`, size `s-2vcpu-4gb`, and that `domain_name` is
> your real domain. If the plan shows anything you didn't expect, stop.

---

### Step 3 — apply (creates real, billable infra)  **[YOU RUN]**

> **ELI5:** This actually builds the droplet and DNS. It starts the ~₹2,000/mo
> meter. Run it yourself; type `yes` when prompted.

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

> You need two: `droplet_ipv4` (SSH target) and `registrar_nameservers`
> (`ns1/ns2/ns3.digitalocean.com`).

---

### Step 5 — delegate DNS at your registrar  **[YOU RUN, manual]**

> **ELI5:** Tell your registrar "DigitalOcean answers DNS for this domain now."
> This is the one step that can't be automated.

At your registrar, set the domain's **nameservers** to the three from Step 4.

> **Deeper:** Propagation is usually minutes, sometimes up to a few hours. Check
> with `nslookup -type=ns <domain>`. Caddy can't issue TLS certs until DNS
> resolves to the droplet, so don't be surprised by cert errors before this lands.

---

### Step 6 — (optional) move Terraform state to Spaces

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

### Step 7 — bootstrap the droplet  **[YOU RUN]**

> **ELI5:** SSH into the new server, get the code, paste your `.env`, run one
> script that installs Docker and starts everything.

```bash
ssh root@<droplet_ipv4>
git clone <your-repo-url> /opt/ai-memory-infra
cd /opt/ai-memory-infra/infra
cp .env.example .env && nano .env        # paste the SAME secrets as local (prod DOMAIN/URLs)
sudo bash ../scripts/bootstrap.sh
```

> **Deeper:** `bootstrap.sh` installs Docker + Compose, sets UFW (22/80/443),
> then `docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d` and
> polls the API. In prod `.env`, set `DASHBOARD_URL=https://dash.<domain>` and
> `DASHBOARD_API_URL=https://memory.<domain>` so CORS + the dashboard work.
> ⚠️ Verify at this point: the `mem0/mem0-api-server` image tag bundles
> `psycopg`/`langchain-neo4j` (older tags need the patch Dockerfile from the mem0
> self-host guide), and a `mem0-dashboard` image exists (else build from the repo).

---

### Step 8 — health check

```bash
curl -fsS https://memory.<domain>/docs >/dev/null && echo OK
```

Then in a browser: `https://dash.<domain>` (dashboard, basic-auth),
`https://graph.<domain>` (Neo4j Browser, basic-auth). `monitor.` activates in
Phase 8.

> **Deeper:** First TLS handshake may take a few seconds while Caddy fetches
> Let's Encrypt certs. If you get cert errors, re-check Step 5 propagation. Logs:
> `docker compose -f docker-compose.yml -f docker-compose.prod.yml logs mem0 --tail 50`.

---

### Done when
API answers over HTTPS, dashboard + Neo4j Browser load behind basic auth, and a
test `POST /memories` round-trips. Then update `STATUS.md`, commit, open the PR
(CI runs), merge → CD deploys. That closes Phase 1; Phase 2 is backup/restore.
