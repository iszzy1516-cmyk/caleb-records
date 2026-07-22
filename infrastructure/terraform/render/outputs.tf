output "api_url" {
  description = "URL of the Render backend API"
  value       = render_web_service.api.url
}

output "postgres_id" {
  description = "Render Postgres instance ID"
  value       = render_postgres.db.id
}
