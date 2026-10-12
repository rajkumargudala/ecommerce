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

# ---------------------------------------------------------------------------
# Observability Stack Variables (Prometheus, Grafana, Loki, Tempo, OpenTelemetry)
# ---------------------------------------------------------------------------
variable "enable_observability" {
  description = "Whether to deploy the full-stack observability suite (Prometheus, Grafana, Loki, Tempo, OpenTelemetry)."
  type        = bool
  default     = false
}

variable "observability_namespace" {
  description = "Kubernetes namespace for the observability stack."
  type        = string
  default     = "monitoring"
}

variable "observability_storage_class" {
  description = "StorageClass for persistent observability data (Prometheus TSDB, Loki logs, Tempo traces)."
  type        = string
  default     = "gp3"
}

variable "enable_prometheus" {
  description = "Whether to deploy Prometheus & Grafana via kube-prometheus-stack."
  type        = bool
  default     = true
}

variable "enable_grafana" {
  description = "Whether to deploy Grafana dashboard UI."
  type        = bool
  default     = true
}

variable "enable_loki" {
  description = "Whether to deploy Loki & Promtail for log aggregation."
  type        = bool
  default     = true
}

variable "enable_tempo" {
  description = "Whether to deploy Grafana Tempo for distributed tracing."
  type        = bool
  default     = true
}

variable "enable_opentelemetry" {
  description = "Whether to deploy the OpenTelemetry Collector."
  type        = bool
  default     = true
}

variable "kube_prometheus_stack_chart_version" {
  description = "Helm chart version for kube-prometheus-stack."
  type        = string
  default     = "66.3.0"
}

variable "loki_chart_version" {
  description = "Helm chart version for Loki."
  type        = string
  default     = "6.24.0"
}

variable "promtail_chart_version" {
  description = "Helm chart version for Promtail."
  type        = string
  default     = "6.16.6"
}

variable "tempo_chart_version" {
  description = "Helm chart version for Tempo."
  type        = string
  default     = "1.17.0"
}

variable "opentelemetry_collector_chart_version" {
  description = "Helm chart version for OpenTelemetry Collector."
  type        = string
  default     = "0.111.1"
}

variable "prometheus_storage_size" {
  description = "Disk storage allocated for Prometheus TSDB."
  type        = string
  default     = "20Gi"
}

variable "prometheus_retention" {
  description = "Prometheus data retention period."
  type        = string
  default     = "15d"
}

variable "grafana_storage_size" {
  description = "Disk storage allocated for Grafana dashboards and settings."
  type        = string
  default     = "10Gi"
}

variable "grafana_admin_password" {
  description = "Admin password for Grafana web console."
  type        = string
  default     = "admin123"
  sensitive   = true
}

variable "loki_storage_size" {
  description = "Disk storage allocated for Loki log persistence."
  type        = string
  default     = "20Gi"
}

variable "tempo_storage_size" {
  description = "Disk storage allocated for Tempo trace persistence."
  type        = string
  default     = "20Gi"
}

variable "tempo_retention" {
  description = "Trace retention period in Tempo."
  type        = string
  default     = "72h"
}


