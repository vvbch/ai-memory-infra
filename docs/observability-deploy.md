# Observability deploy — Prometheus + Grafana on `monitor.{DOMAIN}`

> **Phase 8 / Phase 9 polish.** Prometheus, Grafana, and node-exporter ship behind
> the Docker Compose **`observability` profile** so the default stack stays lean
> (tenet 7). The `monitor.` DNS record and Caddy route are already provisioned;
> this doc covers turning them on.

**Related:** ADR 008 (stack choice), ADR 014 (shift-left `/metrics` target),
`src/observability/` (metric names + dashboard JSON), `docs/architecture.md`.

---

## What you get

| Component | Role | Exposed |
|---|---|---|
| **Prometheus** | Scrapes host + app metrics (15 d retention) | Internal only (`prometheus:9090`) |
| **Grafana** | Dashboards from `src/observability/dashboards/` | `https://monitor.{DOMAIN}` via Caddy |
| **node-exporter** | VPS CPU / memory / disk | Internal only (`node-exporter:9100`) |

Grafana sits behind **two gates**: Caddy basic auth (`BASIC_AUTH_*`, same as
`dash.` / `graph.`) and Grafana's own admin login (`GRAFANA_ADMIN_*`).

**RAM budget:** ~700 MB for the three containers (ADR 008). On the 4 GB droplet,
enable only when steady-state headroom allows; upgrade to 8 GB if the box runs hot.

---

## Prerequisites

1. **Phase 1 stack live** — memory API, Caddy, Terraform DNS including `monitor.`
   (see `docs/setup.md` Phase 1).
2. **`infra/.env` filled** — add Grafana secrets (copy from `.env.example`):
   ```bash
   GRAFANA_ADMIN_USER=admin
   GRAFANA_ADMIN_PASSWORD=<openssl rand -base64 24>
   ```
   Index in the private secrets catalog (ADR 017); never commit the value.
3. **SSH access** to the VPS and the repo checked out under `infra/`.

---

## Enable on the VPS

SSH to the droplet, `cd` into `infra/`, pull latest, then start the prod stack
**with the observability overlay and profile**:

```bash
git pull
docker compose \
  -f docker-compose.yml \
  -f docker-compose.prod.yml \
  -f docker-compose.observability.yml \
  --profile observability \
  up -d
```

Or from the Makefile (Unix/WSL on the VPS):

```bash
make deploy-obs
```

Caddy reloads with the repo's `Caddyfile`, which already reverse-proxies
`monitor.{DOMAIN}` → `grafana:3000`. If Grafana is not running (profile off),
`monitor.` returns **502** — expected until you enable the profile.

---

## Verify

1. **Containers up**
   ```bash
   docker compose -f docker-compose.yml -f docker-compose.prod.yml \
     -f docker-compose.observability.yml --profile observability ps
   ```
   Expect `prometheus`, `grafana`, and `node-exporter` healthy.

2. **Prometheus targets** (on the VPS, internal network)
   ```bash
   docker compose -f docker-compose.yml -f docker-compose.observability.yml \
     --profile observability exec prometheus \
     wget -qO- http://localhost:9090/api/v1/targets | head -c 2000
   ```
   - `node` → **UP**
   - `prometheus` → **UP**
   - `mem0` → **UP** once Mem0 exposes `/metrics`; **DOWN** is OK until ADR 014
     app instrumentation lands (host metrics still flow).

3. **Grafana in browser**
   - Open `https://monitor.<your-domain>/`
   - Caddy basic-auth prompt → `BASIC_AUTH_USER` / password
   - Grafana login → `GRAFANA_ADMIN_USER` / `GRAFANA_ADMIN_PASSWORD`
   - **Dashboards → ai-memory** folder: *Memory Ops*, *Knowledge Growth*

4. **TLS** — first visit may take a few seconds while Caddy issues the
   `monitor.` certificate (same as other subdomains).

---

## Disable (rollback)

Stop observability containers without touching the memory stack:

```bash
docker compose \
  -f docker-compose.yml \
  -f docker-compose.prod.yml \
  -f docker-compose.observability.yml \
  --profile observability \
  down
```

`monitor.{DOMAIN}` will 502 until you re-enable. Core memory API is unaffected.

---

## Local dev (optional)

From `infra/` on a dev machine with `.env` set:

```bash
docker compose \
  -f docker-compose.yml \
  -f docker-compose.observability.yml \
  --profile observability \
  up -d
```

Map `monitor.<DOMAIN>` to `127.0.0.1` in `/etc/hosts` (or use the Windows
equivalent) to exercise the Caddy route locally.

---

## Dashboards & metrics

- **Dashboard JSON:** `src/observability/dashboards/` (provisioned automatically).
- **Metric helpers:** `src/observability/metrics.py` — names used in panels
  (`memory_writes_total`, `retrieval_latency_seconds`, `total_memories`, etc.).
- **Drift / alerts:** `drift_detector.py` and `alerts.py` run outside Grafana
  today (weekly eval gate + future alert wiring). Grafana covers infra + memory
  throughput once `/metrics` is live on Mem0.

To edit a dashboard: change the JSON in-repo, redeploy/restart Grafana, or use
Grafana UI (UI edits persist in the container volume until you export back to git).

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `monitor.` 502 | Observability profile not running | `make deploy-obs` or compose command above |
| Grafana won't start | `GRAFANA_ADMIN_PASSWORD` unset | Set in `infra/.env`, restart grafana |
| Empty memory panels | Mem0 `/metrics` not wired yet | Expected; node-exporter panels still work |
| OOM / slow box | ~700 MB observability overhead | Pause profile or resize droplet (ADR 008) |
| Cert error on `monitor.` | DNS not pointing at droplet | `nslookup monitor.<domain>` |

Logs:

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml \
  -f docker-compose.observability.yml --profile observability \
  logs grafana --tail 50
```

---

## Done when

- `monitor.{DOMAIN}` loads Grafana behind basic auth + Grafana login.
- Prometheus scrapes node-exporter (and mem0 when `/metrics` exists).
- Dashboards visible under the **ai-memory** folder.
- Operator has indexed `GRAFANA_ADMIN_PASSWORD` in the private secrets catalog.
