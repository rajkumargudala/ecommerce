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




