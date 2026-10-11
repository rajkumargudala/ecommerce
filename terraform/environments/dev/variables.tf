variable "region" {
  description = "AWS region."
  type        = string
  default     = "us-east-1"
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
  default     = ["us-east-1a", "us-east-1b", "us-east-1c"]
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
  default = 2
}

variable "node_max_size" {
  type    = number
  default = 6
}

variable "node_desired_size" {
  type    = number
  default = 3
}

variable "ecr_repository_name" {
  description = "Single ECR repository holding all service images."
  type        = string
  default     = "ecommerce-platform"
}

variable "domain_name" {
  description = "Apex domain hosted in Route 53."
  type        = string
  default     = "learnwithmedevops.online"
}

variable "enable_addons" {
  description = "Whether to deploy Kubernetes/Helm addons (gp3 StorageClass, AWS Load Balancer Controller, ArgoCD)."
  type        = bool
  default     = false # Kept false by default to prevent altering existing live resources; enable when deploying next time
}


