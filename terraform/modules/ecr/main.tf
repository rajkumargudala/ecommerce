# A SINGLE ECR repository holding images for ALL services.
#
# ECR has a flat namespace (no real folders), so every service's images live in
# this one repository distinguished by a tag prefix, e.g.:
#   <account>.dkr.ecr.<region>.amazonaws.com/ecommerce-platform:auth-service-<gitsha>-<run-id>-<attempt>
#   <account>.dkr.ecr.<region>.amazonaws.com/ecommerce-platform:frontend-<gitsha>-<run-id>-<attempt>
# CI tags each image with its service name and unique workflow run identity.

resource "aws_ecr_repository" "this" {
  name                 = var.repository_name
  image_tag_mutability = "IMMUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }

  encryption_configuration {
    encryption_type = "AES256"
  }

  tags = var.tags
}

# Retain only the most recent N images to control storage cost.
resource "aws_ecr_lifecycle_policy" "this" {
  repository = aws_ecr_repository.this.name

  policy = jsonencode({
    rules = [
      {
        rulePriority = 1
        description  = "Keep last ${var.max_image_count} images"
        selection = {
          tagStatus   = "any"
          countType   = "imageCountMoreThan"
          countNumber = var.max_image_count
        }
        action = { type = "expire" }
      }
    ]
  })
}
