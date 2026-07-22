output "student_portal_url" {
  description = "URL of the student frontend on Cloudflare Pages"
  value       = "https://${var.student_project_name}.pages.dev"
}

output "staff_portal_url" {
  description = "URL of the staff frontend on Cloudflare Pages"
  value       = "https://${var.staff_project_name}.pages.dev"
}

output "r2_bucket_name" {
  description = "Name of the R2 uploads bucket"
  value       = cloudflare_r2_bucket.uploads.name
}

output "r2_s3_endpoint" {
  description = "S3-compatible endpoint for the R2 bucket"
  value       = "https://${var.cloudflare_account_id}.r2.cloudflarestorage.com"
}

output "r2_public_url" {
  description = "Public download URL for the R2 bucket"
  value       = var.r2_public_url
}

output "r2_access_key_id" {
  description = "R2 S3-compatible access key ID"
  value       = var.r2_access_key_id
  sensitive   = true
}

output "r2_secret_access_key" {
  description = "R2 S3-compatible secret access key"
  value       = var.r2_secret_access_key
  sensitive   = true
}
