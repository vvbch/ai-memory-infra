# ADR 012: Register the domain, host the DNS zone at DigitalOcean

**Status:** Superseded by ADR 016
**Date:** 2026-06-05
**Deciders:** Chandra

### Context

Phase 1 needs a domain and four subdomains (`memory.`, `dash.`, `graph.`,
`monitor.`) pointing at the VPS, served over HTTPS. The IaC tenet (tenet 1) says
no manual console clicks; tenet 7 says fewer moving parts. The droplet, firewall,
and backups bucket already live in DigitalOcean Terraform. The open question was
*where DNS records live* so Terraform can manage them.

### Decision

Register a new domain at a **cheap registrar**, then **delegate its nameservers
to DigitalOcean** so the authoritative DNS **zone lives at DigitalOcean**.
Terraform (`digitalocean_domain` + `digitalocean_record`) then manages every
record with the **same provider and token** already used for the droplet.

The domain name itself is **TBD** — it is a Terraform variable (`domain_name`)
with a placeholder in `terraform.tfvars.example`; it is never hard-coded.

A records created by Terraform: `memory.`, `dash.`, `graph.`, `monitor.`
(+ optional apex) → the droplet's IPv4. `dash.` is included because the OSS Mem0
server compose ships a dashboard container (verified against
`mem0ai/mem0` `server/docker-compose.yaml`).

### Why not alternatives

- **DNS at the registrar:** would split infra across two providers/APIs and
  often means a second Terraform provider (or manual record edits). More moving
  parts, against tenets 1 and 7.
- **Cloudflare DNS:** excellent free tier, but adds a third account/provider and
  token for no Phase-1 benefit; the DO provider already manages everything else.
  Revisit only if we need Cloudflare-specific features (WAF, proxying).
- **Buy the domain *at* DigitalOcean:** DO is not a registrar. Registering at a
  cheap registrar and delegating NS keeps registration cost low while still
  giving Terraform full record control.

### Consequences

- **Positive:** One provider, one token, fully IaC-managed records; clean against
  tenets 1 and 7. Caddy auto-provisions Let's Encrypt TLS for each subdomain.
- **Negative:** One unavoidable manual step — setting the registrar's nameservers
  to `ns1/ns2/ns3.digitalocean.com` (printed by `terraform output
  registrar_nameservers`). This is a one-time delegation, documented, not
  repeated.
- **Cost:** domain ~₹85/mo (~₹1,000/yr registration); DO DNS is ₹0.

---
