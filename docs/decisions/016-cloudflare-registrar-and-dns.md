# ADR 016: Register the domain and host DNS at Cloudflare

**Status:** Accepted
**Date:** 2026-06-07
**Deciders:** the operator
**Supersedes:** ADR 012 (DNS zone at DigitalOcean)

### Context

Phase 1 needs a registered domain and four subdomains (`memory.`, `dash.`, `graph.`,
`monitor.`) pointing at the VPS for Caddy + Let's Encrypt. ADR 012 placed the DNS
zone at DigitalOcean with a cheap third-party registrar (Porkbun/Namecheap) and a
one-time nameserver delegation step.

Tenet 12 requires a deliberate vendor call before committing. the operator chose
**Path B**: Cloudflare as both **registrar and DNS host**, with DigitalOcean
remaining compute-only (droplet, firewall, Spaces).

Verified facts (2026-06-07, sources: Cloudflare docs + RDAP):

- Cloudflare Registrar registers `.dev` at **at-cost** (~$10–12/yr); renewal is
  not marked up.
- Cloudflare Registrar **requires Cloudflare nameservers** — you cannot register
  at Cloudflare and delegate NS to DigitalOcean.
- DigitalOcean is **not a registrar** (unchanged from ADR 012).
- Name chosen: **`example.com`** (`the operator.dev` taken; `example.com` available
  via RDAP). App URL: `memory.example.com`.

### Decision

1. **Register `example.com` at Cloudflare Registrar** (operator-run, before
   `terraform apply` — the zone must exist for Terraform to create records).
2. **Manage DNS A records in Terraform** via the Cloudflare provider
   (`cloudflare_dns_record`), looked up against the existing zone
   (`data.cloudflare_zone`).
3. **Keep compute at DigitalOcean** — droplet, firewall, Spaces unchanged.
4. Set **`proxied = false`** on every A record so traffic goes directly to Caddy
   on the droplet (required for ACME HTTP/TLS-ALPN challenges; Cloudflare proxy
   would intercept and break cert issuance unless we added a more complex
   Full-Strict + origin-cert setup).

### Why not alternatives

- **ADR 012 (DO DNS + Porkbun registrar):** already coded and validated, but
  splits vendors across a small private registrar + DO. the operator prioritized tier-1
  vendor profile (balance sheet, ecosystem, portability) per tenet 12.
- **DNS-only at Cloudflare with registrar elsewhere:** possible, but Cloudflare
  Registrar at-cost with forced CF NS is simpler than two vendors for the same
  outcome.
- **Cloudflare proxy ON (orange cloud):** free CDN/WAF, but breaks naive ACME to
  Caddy; deferred until we explicitly design for it (Phase 8+ if needed).

### Consequences

- **Positive:** Tier-1 registrar + DNS (NET, large-cap); at-cost domain pricing;
  optional WAF/CDN/Tunnel later without changing registrar; Terraform still owns
  every record (tenet 1).
- **Negative:** Two cloud tokens instead of one (DO + Cloudflare); ADR 012 DNS
  block rewritten; **60-day registrar lock** after registration before transfer
  out (Cloudflare policy).
- **Operator steps:** buy the domain at Cloudflare *before* apply; create a CF API
  token (`Zone → DNS → Edit` for `example.com`); no nameserver delegation step.
- **Exit:** `terraform destroy` removes CF DNS records + DO compute; to stop the
  domain bill, disable auto-renew or transfer out after 60 days
  (`docs/decommission.md` §3 Step 3).
- **Cost:** domain ~₹85/mo (~₹1,000/yr at-cost); CF DNS ₹0; DO compute unchanged.

---
