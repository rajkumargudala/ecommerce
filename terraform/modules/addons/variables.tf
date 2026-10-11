variable "cluster_name" {
  description = "EKS cluster name."
  type        = string
}

variable "cluster_endpoint" {
  description = "EKS cluster API endpoint."
  type        = string
}

variable "cluster_certificate_authority_data" {
  description = "EKS cluster CA certificate data."
  type        = string
}

variable "load_balancer_controller_irsa_role_arn" {
  description = "ARN of the IRSA role for AWS Load Balancer Controller."
  type        = string
}

variable "region" {
  description = "AWS region."
  type        = string
  default     = "us-east-1"
}

variable "vpc_id" {
  description = "VPC ID where the EKS cluster resides."
  type        = string
}

variable "enable_aws_load_balancer_controller" {
  description = "Whether to install AWS Load Balancer Controller via Helm."
  type        = bool
  default     = true
}

variable "enable_argocd" {
  description = "Whether to install ArgoCD via Helm."
  type        = bool
  default     = true
}

variable "enable_gp3_storage_class" {
  description = "Whether to create gp3 default StorageClass for EBS CSI driver."
  type        = bool
  default     = true
}

variable "aws_load_balancer_controller_chart_version" {
  description = "Chart version for AWS Load Balancer Controller."
  type        = string
  default     = "3.6.0"
}

variable "argocd_chart_version" {
  description = "Chart version for ArgoCD."
  type        = string
  default     = "10.10.2"
}

