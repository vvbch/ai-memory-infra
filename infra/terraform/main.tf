# Phase 1 infrastructure: one 4GB droplet in Bangalore, a locked-down firewall
# (22/80/443 only), DNS A records at Cloudflare (ADR 016), and a Spaces bucket
# for backups. Everything here is reproducible — no console clicks (tenet 1).

terraform {
  required_version = ">= 1.6.0"

  required_providers {
    digitalocean = {
      source  = "digitalocean/digitalocean"
      version = "~> 2.0"
    }
    cloudflare = {
      source  = "cloudflare/cloudflare"
      version = "~> 5.0"
    }
  }
}

provider "digitalocean" {
  token             = var.do_token
  spaces_access_id  = var.spaces_access_id
  spaces_secret_key = var.spaces_secret_key
}

provider "cloudflare" {
  api_token = var.cloudflare_api_token
}

# ---- SSH key -------------------------------------------------------------

resource "digitalocean_ssh_key" "deploy" {
  name       = var.ssh_key_name
  public_key = var.ssh_public_key
}

# ---- Droplet (the VPS that runs the whole Compose stack) -----------------

resource "digitalocean_droplet" "vps" {
  name       = var.droplet_name
  region     = var.region
  size       = var.droplet_size
  image      = var.droplet_image
  ssh_keys   = [digitalocean_ssh_key.deploy.fingerprint]
  backups    = var.enable_droplet_backups
  monitoring = var.enable_monitoring
  tags       = var.tags

  # Keeps the instance reachable even if an apply wants to replace it.
  lifecycle {
    create_before_destroy = true
  }
}

# ---- Firewall: only 22/80/443 in; everything out -------------------------
# Postgres, Neo4j, and Prometheus never get a public port — only Caddy
# (80/443) faces the internet (ADR 009).

resource "digitalocean_firewall" "vps" {
  name        = "${var.droplet_name}-fw"
  droplet_ids = [digitalocean_droplet.vps.id]
  tags        = var.tags

  inbound_rule {
    protocol         = "tcp"
    port_range       = "22"
    source_addresses = var.ssh_allowed_cidrs
  }

  inbound_rule {
    protocol         = "tcp"
    port_range       = "80"
    source_addresses = ["0.0.0.0/0", "::/0"]
  }

  inbound_rule {
    protocol         = "tcp"
    port_range       = "443"
    source_addresses = ["0.0.0.0/0", "::/0"]
  }

  # Allow all egress (package installs, ACME, DeepSeek/OpenAI APIs, Spaces).
  outbound_rule {
    protocol              = "tcp"
    port_range            = "1-65535"
    destination_addresses = ["0.0.0.0/0", "::/0"]
  }

  outbound_rule {
    protocol              = "udp"
    port_range            = "1-65535"
    destination_addresses = ["0.0.0.0/0", "::/0"]
  }

  outbound_rule {
    protocol              = "icmp"
    destination_addresses = ["0.0.0.0/0", "::/0"]
  }
}

# ---- DNS records at Cloudflare (ADR 016) ---------------------------------
# The zone must already exist — register the domain at Cloudflare Registrar
# before apply. proxied=false so ACME reaches Caddy on the droplet directly.

data "cloudflare_zone" "primary" {
  filter = {
    name = var.domain_name
  }
}

# A record per subdomain (memory./dash./graph./monitor.) -> droplet IPv4.
resource "cloudflare_dns_record" "subdomain_a" {
  for_each = toset(var.subdomains)

  zone_id = data.cloudflare_zone.primary.id
  name    = "${each.value}.${var.domain_name}"
  type    = "A"
  content = digitalocean_droplet.vps.ipv4_address
  ttl     = 300
  proxied = false
}

# Optional apex -> droplet IPv4.
resource "cloudflare_dns_record" "apex_a" {
  count = var.create_apex_record ? 1 : 0

  zone_id = data.cloudflare_zone.primary.id
  name    = var.domain_name
  type    = "A"
  content = digitalocean_droplet.vps.ipv4_address
  ttl     = 300
  proxied = false
}

# ---- Backups bucket (DO Spaces) ------------------------------------------
# Off-box destination for the Phase 2 backup pipeline. Private ACL.
#
# Data-loss hardening (ADR 023 §3, operator-approved 2026-06-08):
#   - versioning ON: an accidental/malicious delete or overwrite leaves the
#     prior copy recoverable (delete → delete-marker, old version retained).
#     DO Spaces supports versioning + lifecycle (API/Terraform) but NOT
#     Object-Lock/WORM (verified vs DO docs; true immutability would need a
#     provider change = tenet 12, out of scope).
#   - lifecycle owns retention server-side, replacing the old client-side
#     `s3cmd del` prune in backup.sh (a buggy/compromised box can no longer
#     wipe every backup; deletion is now a declarative, auditable policy):
#       * current backups expire after 30 days,
#       * noncurrent versions (a deleted/overwritten copy) stay recoverable
#         14 more days, then are purged to bound cost,
#       * expired delete-markers are swept,
#       * incomplete multipart uploads are aborted after 1 day.
# Retention is a TTL one-way door (tenet 17) — these numbers were signed off.

resource "digitalocean_spaces_bucket" "backups" {
  name   = var.backup_bucket_name
  region = var.spaces_region
  acl    = "private"

  versioning {
    enabled = true
  }

  lifecycle_rule {
    id      = "expire-old-backups"
    enabled = true

    abort_incomplete_multipart_upload_days = 1

    expiration {
      days = 30
    }

    noncurrent_version_expiration {
      days = 14
    }
  }

  lifecycle_rule {
    id      = "sweep-expired-delete-markers"
    enabled = true

    expiration {
      expired_object_delete_marker = true
    }
  }
}
