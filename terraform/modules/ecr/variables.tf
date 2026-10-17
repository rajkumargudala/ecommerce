variable "repository_name" {
  description = "Name of the single ECR repository that holds every service image."
  type        = string
}

variable "max_image_count" {
  description = "How many recent images to retain (about 20 full releases at 14 images each)."
  type        = number
  default     = 280
}

variable "tags" {
  description = "Common tags."
  type        = map(string)
  default     = {}
}
