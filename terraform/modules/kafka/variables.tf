variable "name" {
  description = "Name prefix for MSK and credential resources."
  type        = string
}

variable "region" {
  description = "AWS region used for Secrets Manager KMS permissions."
  type        = string
}

variable "kafka_version" {
  description = "Amazon MSK Kafka version."
  type        = string
  default     = "3.9.x"
}

variable "broker_instance_type" {
  description = "MSK broker EC2 instance type."
  type        = string
  default     = "kafka.t3.small"
}

variable "broker_storage_gib" {
  description = "EBS storage per broker in GiB."
  type        = number
  default     = 20
}

variable "broker_count" {
  description = "Number of brokers. Must match private subnet count and be a multiple of Availability Zones."
  type        = number
}

variable "vpc_id" {
  description = "VPC containing EKS and the MSK brokers."
  type        = string
}

variable "private_subnet_ids" {
  description = "Private subnets for MSK brokers."
  type        = list(string)
}

variable "client_security_group_id" {
  description = "EKS node security group allowed to connect to Kafka."
  type        = string
}

variable "oidc_provider_arn" {
  description = "EKS OIDC provider ARN used by the Kafka client IRSA role."
  type        = string
}

variable "oidc_provider" {
  description = "EKS OIDC provider host path used in the IRSA trust policy."
  type        = string
}

variable "namespace" {
  description = "Kubernetes namespace containing Kafka client pods."
  type        = string
  default     = "default"
}

variable "service_account_name" {
  description = "Kubernetes service account bound to the Secrets Manager reader role."
  type        = string
  default     = "ecommerce-kafka-client"
}

variable "tags" {
  description = "Common resource tags."
  type        = map(string)
  default     = {}
}
