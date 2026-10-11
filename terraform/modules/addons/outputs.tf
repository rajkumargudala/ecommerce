output "aws_load_balancer_controller_release_name" {
  description = "Helm release name of the AWS Load Balancer Controller."
  value       = var.enable_aws_load_balancer_controller ? helm_release.aws_load_balancer_controller[0].name : null
}

output "argocd_release_name" {
  description = "Helm release name of ArgoCD."
  value       = var.enable_argocd ? helm_release.argocd[0].name : null
}

# ---------------------------------------------------------------------------
# Observability Stack Outputs
# ---------------------------------------------------------------------------
output "observability_namespace" {
  description = "Kubernetes namespace housing the observability suite."
  value       = var.enable_observability ? kubernetes_namespace_v1.monitoring[0].metadata[0].name : null
}

output "prometheus_service_url" {
  description = "Cluster-internal service URL for Prometheus server."
  value       = var.enable_observability && var.enable_prometheus ? "http://kube-prometheus-stack-prometheus.${var.observability_namespace}.svc.cluster.local:9090" : null
}

output "grafana_service_url" {
  description = "Cluster-internal service URL for Grafana UI."
  value       = var.enable_observability && var.enable_grafana ? "http://kube-prometheus-stack-grafana.${var.observability_namespace}.svc.cluster.local:80" : null
}

output "loki_service_url" {
  description = "Cluster-internal service URL for Loki log push and query API."
  value       = var.enable_observability && var.enable_loki ? "http://loki.${var.observability_namespace}.svc.cluster.local:3100" : null
}

output "tempo_otlp_grpc_endpoint" {
  description = "Cluster-internal OTLP gRPC endpoint for Tempo tracing backend."
  value       = var.enable_observability && var.enable_tempo ? "tempo.${var.observability_namespace}.svc.cluster.local:4317" : null
}

output "opentelemetry_collector_otlp_grpc_endpoint" {
  description = "Cluster-internal OTLP gRPC endpoint for OpenTelemetry Collector."
  value       = var.enable_observability && var.enable_opentelemetry ? "opentelemetry-collector.${var.observability_namespace}.svc.cluster.local:4317" : null
}

output "opentelemetry_collector_otlp_http_endpoint" {
  description = "Cluster-internal OTLP HTTP endpoint for OpenTelemetry Collector."
  value       = var.enable_observability && var.enable_opentelemetry ? "http://opentelemetry-collector.${var.observability_namespace}.svc.cluster.local:4318" : null
}


