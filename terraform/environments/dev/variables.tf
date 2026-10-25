variable "region" {
  description = "AWS region."
  type        = string
  default     = "ap-southeast-2"
}

variable "environment" {
  description = "Environment name."
  type        = string
  default     = "dev"
}

variable "name" {
  description = "Resource name prefix."
  type        = string
  default     = "ecommerce-dev"
}

variable "cluster_name" {
  description = "EKS cluster name."
  type        = string
  default     = "ecommerce-cluster-dev"
}

variable "vpc_cidr" {
  description = "VPC CIDR."
  type        = string
  default     = "10.10.0.0/16"
}

variable "azs" {
  description = "Availability zones."
  type        = list(string)
  default     = ["ap-southeast-2a", "ap-southeast-2b", "ap-southeast-2c"]
}

variable "public_subnets" {
  description = "Public subnet CIDRs."
  type        = list(string)
  default     = ["10.10.0.0/20", "10.10.16.0/20", "10.10.32.0/20"]
}

variable "private_subnets" {
  description = "Private subnet CIDRs."
  type        = list(string)
  default     = ["10.10.128.0/20", "10.10.144.0/20", "10.10.160.0/20"]
}

variable "single_nat_gateway" {
  description = "Use a single NAT gateway (cheaper for dev)."
  type        = bool
  default     = true
}

variable "cluster_version" {
  description = "Kubernetes version."
  type        = string
  default     = "1.35"
}

variable "node_instance_types" {
  description = "Managed node group instance types. "
  type        = list(string)
  default     = ["m7i-flex.large"]
}

variable "node_min_size" {
  type    = number
  default = 3
}

variable "node_max_size" {
  type    = number
  default = 6
}

variable "node_desired_size" {
  type    = number
  default = 6
}

variable "ecr_repository_name" {
  description = "Single ECR repository holding all service images."
  type        = string
  default     = "ecommerce-platform"
}

variable "ecr_ci_account_id" {
  description = "AWS account ID used by GitHub Actions to publish images to this ECR repository."
  type        = string
  default     = "877013879278"
}

variable "domain_name" {
  description = "Apex domain hosted in Route 53."
  type        = string
  default     = "learnwithmedevops.online"
}

variable "enable_addons" {
  description = "Whether to deploy Kubernetes/Helm addons (gp3 StorageClass, AWS Load Balancer Controller, ArgoCD)."
  type        = bool
  default     = true # Kept false by default to prevent altering existing live resources; enable when deploying next time
}

variable "enable_observability" {
  description = "Whether to deploy the full-stack observability suite (Prometheus, Grafana, Loki, Tempo, OpenTelemetry) under addons."
  type        = bool
  default     = true # Kept false by default to prevent altering existing live resources; enable when deploying next time
}



