provider "aws" {
  region = var.region

  default_tags {
    tags = {
      Project     = "ecommerce-platform"
      Environment = var.environment
      ManagedBy   = "terraform"
    }
  }
}
