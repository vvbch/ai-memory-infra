# Phase 1 infrastructure: one 4GB droplet in Bangalore, a locked-down firewall
# (22/80/443 only), the DNS zone + records at DigitalOcean, and a Spaces bucket
# for backups. Everything here is reproducible — no console clicks (tenet 1).

terraform {
  required_version = ">= 1.6.0"

  required_providers {
    digitalocean = {
      source  = "digitalocean/digitalocean"
      version = "~> 2.0"
    }
  }
}

provider "digitalocean" {
  token             = var.do_token
  spaces_access_id  = var.spaces_access_id
  spaces_secret_key = var.spaces_secret_key
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

# ---- DNS zone + records (DECISION 2 / ADR 012) ---------------------------
# The zone is authoritative at DigitalOcean. Delegate the registrar's
# nameservers to ns1/ns2/ns3.digitalocean.com (one-time, manual at registrar),
# then every record below is managed here.

resource "digitalocean_domain" "primary" {
  name = var.domain_name
}

# A record per subdomain (memory./dash./graph./monitor.) -> droplet IPv4.
resource "digitalocean_record" "subdomain_a" {
  for_each = toset(var.subdomains)

  domain = digitalocean_domain.primary.id
  type   = "A"
  name   = each.value
  value  = digitalocean_droplet.vps.ipv4_address
  ttl    = 300
}

# Optional apex (@) -> droplet IPv4.
resource "digitalocean_record" "apex_a" {
  count = var.create_apex_record ? 1 : 0

  domain = digitalocean_domain.primary.id
  type   = "A"
  name   = "@"
  value  = digitalocean_droplet.vps.ipv4_address
  ttl    = 300
}

# ---- Backups bucket (DO Spaces) ------------------------------------------
# Off-box destination for the Phase 2 backup pipeline. Private ACL; versioning
# on so a bad backup can't clobber a good one.

resource "digitalocean_spaces_bucket" "backups" {
  name   = var.backup_bucket_name
  region = var.spaces_region
  acl    = "private"

  versioning {
    enabled = true
  }
}
