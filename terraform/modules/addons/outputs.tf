output "aws_load_balancer_controller_release_name" {
  description = "Helm release name of the AWS Load Balancer Controller."
  value       = var.enable_aws_load_balancer_controller ? helm_release.aws_load_balancer_controller[0].name : null
}

output "argocd_release_name" {
  description = "Helm release name of ArgoCD."
  value       = var.enable_argocd ? helm_release.argocd[0].name : null
}

