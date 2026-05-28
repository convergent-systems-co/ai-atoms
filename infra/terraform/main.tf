terraform {
  required_providers {
    cloudflare = {
      source  = "cloudflare/cloudflare"
      version = "~> 4"
    }
  }
  backend "s3" {
    bucket                      = "cs-tfstate"
    key                         = "ai-atoms/terraform.tfstate"
    region                      = "auto"
    endpoint                    = "https://e1fe0f0ce8ff18da4edc118372c30022.r2.cloudflarestorage.com"
    skip_credentials_validation = true
    skip_metadata_api_check     = true
    skip_region_validation      = true
    force_path_style            = true
  }
}

provider "cloudflare" {
  api_token = var.cloudflare_api_token
}

resource "cloudflare_pages_project" "site" {
  account_id        = var.cloudflare_account_id
  name              = "ai-atoms"
  production_branch = "main"
  build_config {
    build_command   = "cd web && npm install && npm run build"
    destination_dir = "web/dist"
  }
}

resource "cloudflare_record" "apex" {
  zone_id = var.cloudflare_zone_id
  name    = "@"
  type    = "CNAME"
  content = "ai-atoms.pages.dev"
  proxied = true
}

resource "cloudflare_record" "www" {
  zone_id = var.cloudflare_zone_id
  name    = "www"
  type    = "CNAME"
  content = "ai-atoms.pages.dev"
  proxied = true
}
