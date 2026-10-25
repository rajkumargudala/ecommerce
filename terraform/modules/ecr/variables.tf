variable "repository_name" {
  description = "Name of the single ECR repository that holds every service image."
  type        = string
}

variable "max_image_count" {
  description = "How many recent images to retain (about 20 full releases at 14 images each)."
  type        = number
  default     = 280
}

variable "ci_account_id" {
  description = "AWS account ID containing the CI role that publishes images to this repository."
  type        = string
}

variable "tags" {
  description = "Common tags."
  type        = map(string)
  default     = {}
}
