# CA certificates for the managed clusters, passed to the app so it can verify
# managed-DB TLS without disabling certificate checks (DO's CA isn't a public root).

data "digitalocean_database_ca" "postgres" {
  cluster_id = digitalocean_database_cluster.postgres.id
}

data "digitalocean_database_ca" "redis" {
  cluster_id = digitalocean_database_cluster.redis.id
}

output "postgres_ca_cert" {
  description = "CA certificate for verifying the Postgres cluster TLS"
  value       = data.digitalocean_database_ca.postgres.certificate
  sensitive   = true
}

output "redis_ca_cert" {
  description = "CA certificate for verifying the Valkey/Redis cluster TLS"
  value       = data.digitalocean_database_ca.redis.certificate
  sensitive   = true
}
