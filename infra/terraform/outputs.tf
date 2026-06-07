# Outputs used by the deploy step (bootstrap.sh / CD).

output "droplet_ipv4" {
  description = "Public IPv4 of the VPS. SSH target and the IP every DNS A record points at."
  value       = digitalocean_droplet.vps.ipv4_address
}

output "droplet_id" {
  description = "DigitalOcean droplet ID."
  value       = digitalocean_droplet.vps.id
}

output "cloudflare_zone_id" {
  description = "Cloudflare zone ID for the domain (useful for debugging DNS in the CF dashboard)."
  value       = data.cloudflare_zone.primary.id
}

output "subdomain_fqdns" {
  description = "Fully-qualified subdomains now served by Caddy over HTTPS."
  value       = [for s in var.subdomains : "${s}.${var.domain_name}"]
}

output "spaces_bucket_name" {
  description = "Name of the backups bucket."
  value       = digitalocean_spaces_bucket.backups.name
}

output "spaces_bucket_endpoint" {
  description = "S3-compatible endpoint for the backups bucket (used by backup.sh and the remote state backend)."
  value       = "https://${digitalocean_spaces_bucket.backups.region}.digitaloceanspaces.com"
}

output "spaces_bucket_domain" {
  description = "Virtual-hosted bucket domain."
  value       = "${digitalocean_spaces_bucket.backups.name}.${digitalocean_spaces_bucket.backups.region}.digitaloceanspaces.com"
}
