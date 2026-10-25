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

# CI currently runs in a separate AWS account. ECR needs this resource policy
# as well as the CI role's identity policy for cross-account image publishing.
data "aws_iam_policy_document" "ci_access" {
  statement {
    sid    = "AllowCiAccountToPublishImages"
    effect = "Allow"

    principals {
      type        = "AWS"
      identifiers = [var.ci_account_id]
    }

    actions = [
      "ecr:BatchCheckLayerAvailability",
      "ecr:BatchGetImage",
      "ecr:CompleteLayerUpload",
      "ecr:GetDownloadUrlForLayer",
      "ecr:InitiateLayerUpload",
      "ecr:PutImage",
      "ecr:UploadLayerPart",
    ]

  }
}

resource "aws_ecr_repository_policy" "ci_access" {
  repository = aws_ecr_repository.this.name
  policy     = data.aws_iam_policy_document.ci_access.json
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
