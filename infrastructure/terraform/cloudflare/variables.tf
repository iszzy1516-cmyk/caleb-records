variable "cloudflare_account_id" {
  description = "Cloudflare account ID"
  type        = string
}

variable "cloudflare_api_token" {
  description = "Cloudflare API token with R2 and Pages write permissions"
  type        = string
  sensitive   = true
}

variable "github_owner" {
  description = "GitHub username or organization that owns the repo"
  type        = string
  default     = "iszzy1516-cmyk"
}

variable "github_repo" {
  description = "GitHub repository name"
  type        = string
  default     = "caleb-records"
}

variable "api_url" {
  description = "URL of the Render backend API"
  type        = string
  default     = "https://culrecords-api.onrender.com"
}

variable "r2_bucket_name" {
  description = "Name of the Cloudflare R2 bucket for uploads"
  type        = string
  default     = "culrecords-uploads"
}

variable "r2_location" {
  description = "Location hint for the R2 bucket"
  type        = string
  default     = "ENAM"
}

variable "r2_access_key_id" {
  description = "R2 S3-compatible access key ID (for the backend app, not Terraform)"
  type        = string
  sensitive   = true
}

variable "r2_secret_access_key" {
  description = "R2 S3-compatible secret access key (for the backend app, not Terraform)"
  type        = string
  sensitive   = true
}

variable "r2_public_url" {
  description = "Public URL for the R2 bucket after public access is enabled"
  type        = string
}

variable "student_project_name" {
  description = "Cloudflare Pages project name for the student portal"
  type        = string
  default     = "culrecords-student"
}

variable "staff_project_name" {
  description = "Cloudflare Pages project name for the staff portal"
  type        = string
  default     = "culrecords-staff"
}
