# Remote state in DigitalOcean Spaces (S3-compatible) so state isn't local-only
# (tenet 1). DO Spaces speaks the S3 protocol, so Terraform's built-in "s3"
# backend works with a few "skip_*" flags and a custom endpoint.
#
# Chicken-and-egg: the backend bucket must exist BEFORE `terraform init` can use
# it, but this same config also creates a Spaces bucket. So the bootstrap order
# is:
#
#   1. First apply runs with LOCAL state (this block stays commented out):
#        terraform init
#        terraform apply        # creates the droplet, DNS, and Spaces bucket
#   2. Create a small, dedicated state bucket once (separate from backups), e.g.
#      in the DO console or:  s3cmd mb s3://ai-memory-infra-tfstate
#   3. Uncomment the block below, then migrate local state into Spaces:
#        export AWS_ACCESS_KEY_ID=<spaces_access_id>
#        export AWS_SECRET_ACCESS_KEY=<spaces_secret_key>
#        terraform init -migrate-state
#
# Credentials are read from AWS_ACCESS_KEY_ID / AWS_SECRET_ACCESS_KEY (your
# Spaces keys) — never hard-code them here.

# terraform {
#   backend "s3" {
#     bucket = "ai-memory-infra-tfstate"
#     key    = "phase-1/terraform.tfstate"
#     region = "us-east-1" # dummy value; DO ignores it but the s3 backend requires one
#
#     endpoints = {
#       s3 = "https://sgp1.digitaloceanspaces.com" # match your spaces_region
#     }
#
#     skip_credentials_validation = true
#     skip_metadata_api_check     = true
#     skip_region_validation      = true
#     skip_requesting_account_id  = true
#     use_path_style              = false
#   }
# }
