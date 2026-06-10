# Input variables for the ai-memory-infra Phase 1 stack.
# Real values live in terraform.tfvars (gitignored) or TF_VAR_* env vars.
# Secrets are marked `sensitive` so they never print in plan/apply output.

# ---- Credentials ---------------------------------------------------------

variable "do_token" {
  description = "DigitalOcean API token (read/write). Provisions the droplet, firewall, and Spaces bucket."
  type        = string
  sensitive   = true
}

variable "cloudflare_api_token" {
  description = "Cloudflare API token with Zone → DNS → Edit for the domain zone (ADR 016). Create at dash.cloudflare.com/profile/api-tokens."
  type        = string
  sensitive   = true
}

variable "spaces_access_id" {
  description = "DigitalOcean Spaces access key ID (separate from the API token; created under API > Spaces Keys). Used for the backups bucket and remote state."
  type        = string
  sensitive   = true
}

variable "spaces_secret_key" {
  description = "DigitalOcean Spaces secret key paired with spaces_access_id."
  type        = string
  sensitive   = true
}

# ---- Domain & DNS (ADR 016) ---------------------------------------------
# Domain registered at Cloudflare Registrar; DNS A records managed here.
# Register the name and create the zone *before* terraform apply.

variable "domain_name" {
  description = "Registered apex domain at Cloudflare, e.g. chandrav.dev. No default on purpose — set it in terraform.tfvars."
  type        = string

  validation {
    condition     = can(regex("^[a-z0-9.-]+\\.[a-z]{2,}$", var.domain_name))
    error_message = "domain_name must be a bare apex domain like example.com (no scheme, no trailing dot)."
  }
}

variable "subdomains" {
  description = "Subdomains to create A records for, each pointing at the droplet. `dash` is included because the OSS Mem0 server compose ships a mem0-dashboard container (verified against mem0ai/mem0 server/docker-compose.yaml). `mcp` is the remote Streamable HTTP MCP endpoint for Claude connector clients (ADR 034)."
  type        = list(string)
  default     = ["memory", "dash", "graph", "monitor", "mcp"]
}

variable "create_apex_record" {
  description = "Also point the apex (@) at the droplet. Handy for a landing page; harmless if unused."
  type        = bool
  default     = true
}

# ---- Droplet (the VPS) ---------------------------------------------------

variable "droplet_name" {
  description = "Name shown in the DO console."
  type        = string
  default     = "ai-memory-infra"
}

variable "region" {
  description = "DigitalOcean region for the droplet. blr1 = Bangalore (lowest latency from India)."
  type        = string
  default     = "blr1"
}

variable "droplet_size" {
  description = "Droplet slug. s-2vcpu-4gb is the 4GB plan (~₹2,000/mo) sized for the full Compose stack in Phase 1."
  type        = string
  default     = "s-2vcpu-4gb"
}

variable "droplet_image" {
  description = "Base image slug."
  type        = string
  default     = "ubuntu-24-04-x64"
}

variable "enable_droplet_backups" {
  description = "DO weekly droplet snapshots add ~20% to the droplet bill. We back up at the app layer (pg_dump + neo4j dump -> Spaces, Phase 2), so default off (tenet 6)."
  type        = bool
  default     = false
}

variable "enable_monitoring" {
  description = "Install the free DO monitoring agent (feeds Phase 8 observability). No extra cost."
  type        = bool
  default     = true
}

# ---- SSH access ----------------------------------------------------------

variable "ssh_key_name" {
  description = "Name for the SSH key as stored in DigitalOcean."
  type        = string
  default     = "ai-memory-infra"
}

variable "ssh_public_key" {
  description = "Contents of your SSH public key (e.g. ~/.ssh/id_ed25519.pub). Terraform uploads it and grants it root login on the droplet."
  type        = string
}

# ---- Firewall ------------------------------------------------------------

variable "ssh_allowed_cidrs" {
  description = "Source CIDRs allowed to reach SSH (22). Default is open; tighten to your IP/VPN for production (tenet: security)."
  type        = list(string)
  default     = ["0.0.0.0/0", "::/0"]
}

# ---- Backups bucket (DO Spaces) -----------------------------------------
# Spaces is not offered in blr1; sgp1 (Singapore) is the closest region.

variable "spaces_region" {
  description = "Region for the Spaces backups bucket. blr1 has no Spaces, so sgp1 (Singapore) is the nearest option."
  type        = string
  default     = "sgp1"
}

variable "backup_bucket_name" {
  description = "Globally-unique name for the backups bucket. Must be DNS-compatible and unique across all of DO Spaces."
  type        = string
  default     = "ai-memory-infra-backups"
}

variable "tags" {
  description = "Tags applied to droplet/firewall for grouping and billing visibility."
  type        = list(string)
  default     = ["ai-memory-infra", "phase-1"]
}
