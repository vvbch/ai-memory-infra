# Outputs used by the deploy step (bootstrap.sh / CD) and printed for the
# one manual step that can't be automated: nameserver delegation at the registrar.

output "droplet_ipv4" {
  description = "Public IPv4 of the VPS. SSH target and the IP every DNS A record points at."
  value       = digitalocean_droplet.vps.ipv4_address
}

output "droplet_id" {
  description = "DigitalOcean droplet ID."
  value       = digitalocean_droplet.vps.id
}

output "registrar_nameservers" {
  description = "Set these as the nameservers at your registrar to delegate DNS to DigitalOcean (one-time manual step)."
  value = [
    "ns1.digitalocean.com",
    "ns2.digitalocean.com",
    "ns3.digitalocean.com",
  ]
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
