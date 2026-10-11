variable "domain_name" {
  description = "The apex domain name for the ACM certificate."
  type        = string
}

variable "subject_alternative_names" {
  description = "Additional domain names to include in the certificate (e.g. wildcards)."
  type        = list(string)
  default     = []
}

variable "tags" {
  description = "Tags to apply to resources."
  type        = map(string)
  default     = {}
}

