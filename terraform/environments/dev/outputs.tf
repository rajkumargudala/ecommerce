output "vpc_id" {
  value = module.vpc.vpc_id
}

output "private_subnet_ids" {
  value = module.vpc.private_subnet_ids
}

output "public_subnet_ids" {
  value = module.vpc.public_subnet_ids
}

output "eks_cluster_role_arn" {
  value = module.iam.cluster_role_arn
}

output "eks_node_role_arn" {
  value = module.iam.node_role_arn
}

output "cluster_endpoint" {
  value = module.eks.cluster_endpoint
}

output "cluster_name" {
  value = module.eks.cluster_name
}

output "oidc_provider_arn" {
  value = module.eks.oidc_provider_arn
}

output "ecr_repository_url" {
  value = module.ecr.repository_url
}

output "kafka_cluster_arn" {
  description = "Amazon MSK cluster ARN."
  value       = module.kafka.cluster_arn
}

output "kafka_bootstrap_brokers_sasl_scram" {
  description = "TLS bootstrap broker list for SASL/SCRAM clients."
  value       = module.kafka.bootstrap_brokers_sasl_scram
}

output "kafka_scram_secret_arn" {
  description = "Secrets Manager ARN containing the MSK SCRAM username and password."
  value       = module.kafka.scram_secret_arn
}

output "kafka_secret_reader_role_arn" {
  description = "IRSA role ARN used by Kafka client pods to read the SCRAM secret."
  value       = module.kafka.secret_reader_role_arn
}

output "load_balancer_controller_irsa_role_arn" {
  value = module.eks.load_balancer_controller_irsa_role_arn
}

output "acm_certificate_arn" {
  value       = module.acm.certificate_arn
  description = "The ARN of the ACM certificate for learnwithmedevops.online"
}

output "addons_aws_load_balancer_controller" {
  value       = var.enable_addons ? module.addons[0].aws_load_balancer_controller_release_name : null
  description = "Helm release name for AWS Load Balancer Controller."
}

output "addons_argocd" {
  value       = var.enable_addons ? module.addons[0].argocd_release_name : null
  description = "Helm release name for ArgoCD."
}

output "observability_namespace" {
  value       = var.enable_addons && var.enable_observability ? module.addons[0].observability_namespace : null
  description = "Kubernetes namespace housing the observability suite."
}

output "observability_grafana_url" {
  value       = var.enable_addons && var.enable_observability ? module.addons[0].grafana_service_url : null
  description = "Internal service URL for Grafana UI."
}

output "observability_prometheus_url" {
  value       = var.enable_addons && var.enable_observability ? module.addons[0].prometheus_service_url : null
  description = "Internal service URL for Prometheus server."
}

output "observability_loki_url" {
  value       = var.enable_addons && var.enable_observability ? module.addons[0].loki_service_url : null
  description = "Internal service URL for Loki log aggregation."
}

output "observability_tempo_endpoint" {
  value       = var.enable_addons && var.enable_observability ? module.addons[0].tempo_otlp_grpc_endpoint : null
  description = "Internal OTLP gRPC endpoint for Tempo distributed tracing."
}

output "observability_opentelemetry_collector_endpoint" {
  value       = var.enable_addons && var.enable_observability ? module.addons[0].opentelemetry_collector_otlp_grpc_endpoint : null
  description = "Internal OTLP gRPC endpoint for OpenTelemetry Collector."
}





