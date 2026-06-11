# ADR 019: Compute provider — DigitalOcean droplet (BLR1)

**Status:** Accepted
**Date:** 2026-06-07
**Deciders:** the operator

### Context

Phase 1 runs the whole stack — Mem0 (FastAPI) + PostgreSQL/pgvector + Neo4j + Caddy
+ Prometheus/Grafana — as a Docker Compose deployment on a single always-on Linux
VM. DigitalOcean (a 4 GB droplet in BLR1/Bangalore) was assumed from early on and is
baked into the Terraform and `architecture.md`, but the compute-provider choice was
never written up. Tenet 12 requires every external dependency to be deliberated and
documented *before* committing recurring spend; this ADR closes that gap, prompted by
the operator's pre-`apply` question ("is DO the cost floor / is its reliability and
latency acceptable vs AWS/GCP/Azure?").

### Verified facts (2026-06-07, sources: provider pricing pages + 2026 comparisons)

For a 2 vCPU / 4 GB instance:

| Provider | Price/mo | India DC | Egress | SLA |
|---|---|---|---|---|
| **DigitalOcean** BLR1 | **$24** | ✅ Bangalore (5–15 ms) | 4 TB incl., $0.01/GB over | **99.99%** |
| AWS Lightsail | $20 | ✅ Mumbai | 4–5 TB, **$0.09/GB over (9×)** | per AWS |
| Vultr / Linode | ~$24 | ✅ Mumbai | comparable | varies |
| GCP e2 / Azure B2s | ~$24–30+ | ✅ Mumbai/Pune | **metered egress** | varies |
| Hetzner CPX22 | **~$9.49** (post-Apr-2026) | ❌ nearest Singapore (+40–60 ms) | 20 TB incl. | **none published** |

DO moves to per-second billing (60s min) from Jan 2026 — flat monthly cap unchanged.

### Decision

**Use a single DigitalOcean 4 GB droplet in BLR1 for Phase 1 compute** (droplet +
cloud firewall + Spaces for backups/state). Single-node by design — **no HA**.

Weighed on the tenet-12 dimensions:

1. **Total cost incl. exit.** $24/mo flat is at the floor among mainstream,
   India-region, flat-rate providers (ties Vultr/Linode; Lightsail is $4 less but its
   9× egress overage is the variable-cost trap tenet 15 rejects). Running the same
   services as managed products (Neo4j Aura + managed Postgres) would be $50–100+/mo.
   **Exit cost is near-zero** — see portability.
2. **Portability / lock-in.** It's plain Docker Compose on a vanilla Linux VM, so
   migrating to Hetzner / AWS / a local Alienware box is a re-provision + restore, not
   a rewrite (tenet 2). Nothing DO-proprietary is in the critical path.
3. **Reliability & track record.** Published **99.99% droplet SLA** (better than
   Hetzner's none); mature, well-documented platform. Fault tolerance for *this*
   workload is **tenet 4 (graceful degradation)** — if the VPS is down, every LLM
   still works with its native memory — plus **backups → Spaces** (Phase 2) for data
   durability, not live multi-node replication (which would violate tenets 6 & 7 for
   negligible benefit at personal-project stakes).
4. **Company viability.** DO is a public company (NYSE: DOCN), profitable, long-lived
   in the developer-VPS niche; low discontinuation risk over 5–10 yr.
5. **Ecosystem & standards.** Standard Linux + S3-compatible Spaces + Terraform
   provider; nothing exotic. Bangalore region is a decisive latency win for an
   India-resident operator (5–15 ms vs Hetzner Singapore's +40–60 ms).

### Why not the alternatives

- **Hetzner** is the true price floor (~60% cheaper) but has **no India datacenter**
  (Singapore latency) and **no published SLA** — a real trade-off for a
  latency-sensitive India user, not a free win. Documented as the **fallback** if
  latency tolerance changes or for a non-India workload.
- **AWS Lightsail** ties on price but its **$0.09/GB egress overage** makes the bill
  unpredictable (against tenet 15); raw EC2/GCE/Azure VMs are pricier once storage +
  metered egress are added, and more complex (tenets 6, 7) with no single-node upside.
- **Managed databases / multi-AZ HA** rejected for Phase 1: multiplies cost and moving
  parts; the stakes don't justify it (tenets 4, 6, 7).

### Consequences

- **Positive:** lowest-latency India option at a predictable flat rate (tenet 15),
  low ops (tenet 7), published SLA, clean documented exit (tenet 12).
- **Negative:** ~60% pricier than Hetzner; single-node means a droplet outage takes
  the memory layer down until restored (accepted — tenet 4 covers the UX).
- **Exit / reversibility:** `terraform destroy` (or `docs/decommission.md` →
  `teardown.py`) drops the droplet in one command; the Compose stack redeploys on any
  Linux host from the same repo + a Spaces restore.
- **Revisit triggers:** sustained cost pressure post-income-change, a need for HA, or
  the Alienware local-inference path maturing → re-evaluate (Hetzner or self-host).
