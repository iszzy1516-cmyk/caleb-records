variable "render_api_key" {
  description = "Render API key"
  type        = string
  sensitive   = true
}

variable "render_owner_id" {
  description = "Render owner ID (team or user ID)"
  type        = string
}

variable "region" {
  description = "Render region"
  type        = string
  default     = "oregon"
}

variable "web_service_plan" {
  description = "Render web service plan"
  type        = string
  default     = "free"
}

variable "postgres_plan" {
  description = "Render Postgres plan"
  type        = string
  default     = "free"
}

variable "repo_url" {
  description = "GitHub repo URL"
  type        = string
  default     = "https://github.com/iszzy1516-cmyk/caleb-records"
}

variable "dockerfile_path" {
  description = "Path to backend Dockerfile relative to repo root"
  type        = string
  default     = "backend/Dockerfile"
}

variable "docker_context" {
  description = "Docker build context relative to repo root"
  type        = string
  default     = "backend"
}

variable "student_portal_url" {
  description = "Cloudflare Pages URL for student frontend"
  type        = string
  default     = "https://culrecords-student.pages.dev"
}

variable "staff_portal_url" {
  description = "Cloudflare Pages URL for staff frontend"
  type        = string
  default     = "https://culrecords-staff.pages.dev"
}

variable "r2_bucket_name" {
  description = "Cloudflare R2 bucket name"
  type        = string
  default     = "culrecords-uploads"
}

variable "r2_endpoint_url" {
  description = "R2 S3-compatible endpoint"
  type        = string
  default     = "https://4dc9fb0f26d0cd221ffe7faa30155e47.r2.cloudflarestorage.com"
}

variable "r2_public_url" {
  description = "R2 public URL for downloads"
  type        = string
  default     = "https://pub-13d1a4322396452e8a84fe7cdbcdaab9.r2.dev"
}

variable "r2_access_key_id" {
  description = "R2 S3 access key ID"
  type        = string
  sensitive   = true
}

variable "r2_secret_access_key" {
  description = "R2 S3 secret access key"
  type        = string
  sensitive   = true
}

variable "dashscope_api_key" {
  description = "DashScope API key for Qwen vision model"
  type        = string
  sensitive   = true
  default     = ""
}

variable "vision_verify_uploads" {
  description = "Enable vision verification on uploads"
  type        = string
  default     = "false"
}

variable "smtp_host" {
  type    = string
  default = ""
}

variable "smtp_port" {
  type    = string
  default = "587"
}

variable "smtp_user" {
  type    = string
  default = ""
}

variable "smtp_password" {
  type      = string
  sensitive = true
  default   = ""
}

variable "smtp_from" {
  type    = string
  default = "noreply@calebuniversity.edu.ng"
}
