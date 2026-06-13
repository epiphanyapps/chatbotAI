# Networking Module Outputs

output "vpc_id" {
  description = "VPC ID"
  value       = digitalocean_vpc.main.id
}

output "vpc_cidr" {
  description = "VPC CIDR block"
  value       = digitalocean_vpc.main.ip_range
}

# NOTE: Firewalls are disabled for App Platform deployments
# These outputs are preserved for Droplet-based deployments
output "web_firewall_id" {
  description = "Web firewall ID (null for App Platform)"
  value       = null
}

output "database_firewall_id" {
  description = "Database firewall ID (null for App Platform)"
  value       = null
}

output "reserved_ip" {
  description = "Reserved IP address (if created)"
  value       = length(digitalocean_reserved_ip.main) > 0 ? digitalocean_reserved_ip.main[0].ip_address : null
}

output "domain_name" {
  description = "Managed domain name (if created)"
  value       = length(digitalocean_domain.main) > 0 ? digitalocean_domain.main[0].name : null
}