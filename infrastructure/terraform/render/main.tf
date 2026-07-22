terraform {
  required_version = ">= 1.0"
  required_providers {
    render = {
      source  = "render-oss/render"
      version = "~> 1.0"
    }
  }
}

provider "render" {
  api_key  = var.render_api_key
  owner_id = var.render_owner_id
}

resource "render_postgres" "db" {
  name          = "culrecords-db"
  plan          = var.postgres_plan
  region        = var.region
  version       = "16"
  database_name = "calebrecords"
  database_user = "calebrecords"
}

resource "render_web_service" "api" {
  name              = "culrecords-api"
  plan              = var.web_service_plan
  region            = var.region
  health_check_path = "/health"

  maintenance_mode = null

  lifecycle {
    ignore_changes = [
      notification_override,
      previews,
      pull_request_previews_enabled,
      log_stream_override,
      max_shutdown_delay_seconds,
      num_instances,
      root_directory,
      active_custom_domains,
      env_vars["SECRET_KEY"].value,
    ]
  }

  runtime_source = {
    docker = {
      auto_deploy     = true
      branch          = "main"
      repo_url        = var.repo_url
      dockerfile_path = var.dockerfile_path
      context         = var.docker_context
    }
  }

  env_vars = {
    DATABASE_URL = {
      value = render_postgres.db.connection_info.internal_connection_string
    }
    SECRET_KEY = {
      generate_value = true
    }
    CORS_ORIGINS = {
      value = "${var.student_portal_url},${var.staff_portal_url},https://tauri.localhost,tauri://localhost,http://localhost:5173,http://localhost:5174,http://localhost:8000"
    }
    FRONTEND_URL = {
      value = var.student_portal_url
    }
    UPLOAD_DIR = {
      value = "/app/uploads"
    }
    MAX_FILE_SIZE = {
      value = "10485760"
    }
    S3_UPLOAD_BUCKET = {
      value = var.r2_bucket_name
    }
    AWS_REGION = {
      value = "auto"
    }
    S3_ENDPOINT_URL = {
      value = var.r2_endpoint_url
    }
    S3_PUBLIC_URL = {
      value = var.r2_public_url
    }
    AWS_ACCESS_KEY_ID = {
      value = var.r2_access_key_id
    }
    AWS_SECRET_ACCESS_KEY = {
      value = var.r2_secret_access_key
    }
    VISION_PROVIDER = {
      value = "dashscope"
    }
    DASHSCOPE_BASE_URL = {
      value = "https://dashscope-intl.aliyuncs.com/compatible-mode/v1"
    }
    DASHSCOPE_MODEL = {
      value = "qwen-vl-max"
    }
    DASHSCOPE_API_KEY = {
      value = var.dashscope_api_key
    }
    VISION_VERIFY_UPLOADS = {
      value = "true"
    }
    VISION_REJECT_ON_FAILURE = {
      value = "true"
    }
    VISION_MIN_CONFIDENCE = {
      value = "0.7"
    }
    SMTP_HOST = {
      value = var.smtp_host
    }
    SMTP_PORT = {
      value = var.smtp_port
    }
    SMTP_USER = {
      value = var.smtp_user
    }
    SMTP_PASSWORD = {
      value = var.smtp_password
    }
    SMTP_FROM = {
      value = var.smtp_from
    }
  }
}
