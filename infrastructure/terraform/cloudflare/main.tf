terraform {
  required_version = ">= 1.0"
  required_providers {
    cloudflare = {
      source  = "cloudflare/cloudflare"
      version = "~> 4.0"
    }
  }
}

provider "cloudflare" {
  api_token = var.cloudflare_api_token
}

# R2 bucket for document uploads
resource "cloudflare_r2_bucket" "uploads" {
  account_id = var.cloudflare_account_id
  name       = var.r2_bucket_name
  location   = var.r2_location
}

# Student frontend
resource "cloudflare_pages_project" "student" {
  account_id        = var.cloudflare_account_id
  name              = var.student_project_name
  production_branch = "main"

  build_config {
    build_command   = "npm ci && npm run build"
    destination_dir = "dist"
    root_dir        = "frontend"
  }

  source {
    type = "github"
    config {
      owner                         = var.github_owner
      repo_name                     = var.github_repo
      production_branch             = "main"
      production_deployment_enabled = true
      deployments_enabled           = true
      pr_comments_enabled           = true
      preview_branch_includes       = ["*"]
      preview_branch_excludes       = []
      preview_deployment_setting    = "all"
    }
  }

  deployment_configs {
    production {
      environment_variables = {
        VITE_API_URL = var.api_url
        NODE_VERSION = "20"
      }
    }
    preview {
      environment_variables = {
        VITE_API_URL = var.api_url
        NODE_VERSION = "20"
      }
    }
  }
}

# Staff frontend
resource "cloudflare_pages_project" "staff" {
  account_id        = var.cloudflare_account_id
  name              = var.staff_project_name
  production_branch = "main"

  build_config {
    build_command   = "npm ci && npm run build"
    destination_dir = "dist"
    root_dir        = "frontend-staff"
  }

  source {
    type = "github"
    config {
      owner                         = var.github_owner
      repo_name                     = var.github_repo
      production_branch             = "main"
      production_deployment_enabled = true
      deployments_enabled           = true
      pr_comments_enabled           = true
      preview_branch_includes       = ["*"]
      preview_branch_excludes       = []
      preview_deployment_setting    = "all"
    }
  }

  deployment_configs {
    production {
      environment_variables = {
        VITE_API_URL = var.api_url
        NODE_VERSION = "20"
      }
    }
    preview {
      environment_variables = {
        VITE_API_URL = var.api_url
        NODE_VERSION = "20"
      }
    }
  }
}
