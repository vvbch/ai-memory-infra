# Decommission, Rollback & Estate Runbook

> **The exit path (tenet 12).** Anything we turn on, we must be able to cleanly
> turn off — to stop spending money tomorrow, or so that **someone who is not an
> engineer** (a family member, an executor) can shut everything down if I no
> longer can. This file is that procedure. It is written to be followed
> top-to-bottom by a careful non-expert.
>
> Three situations, in order of severity:
> 1. **Rollback** — a deploy went bad; go back to the last working version. (Infra stays.)
> 2. **Pause** — stop the bills for a while but keep the option to come back.
> 3. **Full decommission** — shut it all down permanently and stop every charge.

---

## 0. Where the keys live (READ FIRST)

This repository contains **no passwords or secrets** on purpose. To do anything
below you need the credentials, which are stored **outside** this repo:

- **Password manager** (entry group: `ai-memory-infra`) — DigitalOcean login,
  registrar login, OpenAI login, and the SSH private key passphrase.
- **The SSH private key file** — on the operator's main machine at
  `~/.ssh/id_ed25519` (Windows: `C:\Users\<user>\.ssh\id_ed25519`).

> **For an executor:** if you have the password-manager master password, you have
> everything. Each account below is reachable by logging in on its website.

The three companies that bill money are: **DigitalOcean** (the server, ~₹2,000/mo),
the **domain registrar** (the web address, ~₹1,000/yr), and **OpenAI**
(pay-per-use, only while the memory system is running). Stopping all charges =
dealing with these three.

---

## 1. Rollback — undo a bad deploy (infra stays up)

**ELI5:** the website is broken after an update; put the previous working version
back. This does *not* delete anything — it just re-runs the last good build.

The app runs as Docker containers on the server, pinned to image versions in
`infra/.env` (`MEM0_IMAGE_TAG`, etc.). Rolling back = pointing those back to the
previous tag and restarting.

```bash
ssh root@<droplet_ipv4>                       # log into the server
cd /opt/ai-memory-infra
git log --oneline -5                          # find the last good commit
git checkout <last-good-commit> -- infra/.env # or hand-edit the *_IMAGE_TAG values
cd infra
make deploy                                   # pull those image tags + restart
make health                                   # expect "OK"
```

> **Deeper:** this mirrors what CD does automatically — deploy → health-check →
> on failure, redeploy the previous image (AGENTS.md "CD" line). Doing it by hand
> is the manual version of that safety net. Nothing here touches the database, so
> your memories are preserved across a rollback.

If a rollback isn't enough and you need the data back, that's **restore**, not
rollback — see `scripts/restore.sh` (Phase 2 backup/restore).

---

## 2. Pause — stop most spend, keep the option to return

**ELI5:** mothball it. Keep the domain and accounts, but stop the big monthly
server bill. You can rebuild later from this repo in ~15 minutes.

1. **(Optional but recommended) take a final backup** so you can restore later:
   ```bash
   ssh root@<droplet_ipv4> "cd /opt/ai-memory-infra && bash scripts/backup.sh"
   ```
   Confirm the backup landed in the DigitalOcean Spaces bucket.
2. **Destroy the billable infra** (server, firewall, DNS, backups bucket) — this
   is the same one command as a full teardown, but you keep the accounts open:
   ```bash
   python scripts/teardown.py            # preview, confirm, destroy
   ```
3. **Keep**: the domain (let it renew), the DO account, the OpenAI key.
4. **To come back later:** follow `docs/setup.md` from Step 0 — the IaC rebuilds
   everything identically, then `scripts/restore.sh` reloads the backup.

> The server is the ~₹2,000/mo line item; destroying it stops that immediately.
> The domain (~₹1,000/yr) and idle OpenAI key cost ~nothing while paused.

---

## 3. Full decommission — shut everything down permanently

**ELI5:** turn it all off and make sure **no company can charge anything ever
again.** Do the steps in order. Steps 1 is automated; 2–5 are website clicks.

### Step 1 — destroy all cloud infrastructure (automated)

```bash
python scripts/teardown.py
```

This shows you exactly what will be deleted (read it like a receipt), asks you to
type the domain name to confirm, then deletes the server, firewall, DNS records,
and backups bucket. When it finishes it prints the manual checklist below.

> Windows without `make`/python on PATH? Run the same destroy directly:
> `terraform -chdir=infra/terraform plan -destroy` then `... apply` once you've
> read it. The Python script just adds the confirmation + checklist around it.

### Step 2 — DigitalOcean: delete leftovers + close billing

1. Log in at **cloud.digitalocean.com**.
2. **Spaces** → if a small bucket whose name ends in **`-tfstate`** still exists
   (the Terraform "memory" bucket, created by hand), open it → **empty** it →
   **destroy** it. (Terraform doesn't own this one.)
3. **Droplets / Networking** → confirm the list is **empty** (teardown should
   have cleared them).
4. **Settings → Billing** → confirm balance is ₹0, then **Close account**.

### Step 3 — the domain registrar: stop the yearly renewal

1. Log in to whichever registrar the domain was bought from (in the password
   manager).
2. Find the domain → **turn OFF auto-renew**. It will simply expire on its renewal
   date and cost nothing further. (Or delete/cancel it outright if available.)

### Step 4 — OpenAI: revoke the key, stop billing

1. **platform.openai.com → API keys** → **revoke** the project key.
2. **Settings → Billing** → remove the payment method (or set the monthly limit to
   $0). Pay-per-use charges stop the moment the server is gone in Step 1; this
   makes it permanent.

### Step 5 — local machine cleanup (optional, no cost impact)

```powershell
schtasks /Delete /TN "AI-Memory Repo Health" /F     # remove the daily health task (Windows)
```
Delete `.git/hooks/pre-commit` in each repo if you want. The repos themselves can
be archived on GitHub or kept — they hold no secrets.

### Done when
No droplets in DO, balance ₹0, registrar auto-renew off, OpenAI key revoked. From
that point **nothing recurring is billable.**

---

## Quick reference

| I want to… | Do this |
|---|---|
| Undo a bad update | §1 Rollback (`make deploy` to a previous image tag) |
| Stop the big bill but keep my domain | §2 Pause (`python scripts/teardown.py`, keep accounts) |
| Shut it all down forever | §3 Full decommission (teardown + close all 3 accounts) |
| Bring a paused system back | `docs/setup.md` from Step 0, then `scripts/restore.sh` |

> Recovery from a corrupted local repo (a different kind of "rollback") lives in
> `docs/runbook.md` → "On a RED check — re-clone".
