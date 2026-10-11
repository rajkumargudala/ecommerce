# Dev environment: full AWS foundation for the platform.

data "aws_caller_identity" "current" {}

module "vpc" {
  source = "../../modules/vpc"

  name               = var.name
  cidr               = var.vpc_cidr
  azs                = var.azs
  public_subnets     = var.public_subnets
  private_subnets    = var.private_subnets
  cluster_name       = var.cluster_name
  single_nat_gateway = var.single_nat_gateway
}

module "iam" {
  source = "../../modules/iam"

  name = var.name
}

module "eks" {
  source = "../../modules/eks"

  cluster_name       = var.cluster_name
  cluster_version    = var.cluster_version
  vpc_id             = module.vpc.vpc_id
  private_subnet_ids = module.vpc.private_subnet_ids
  cluster_role_arn   = module.iam.cluster_role_arn
  node_role_arn      = module.iam.node_role_arn

  node_instance_types = var.node_instance_types
  node_min_size       = var.node_min_size
  node_max_size       = var.node_max_size
  node_desired_size   = var.node_desired_size
}

module "ecr" {
  source = "../../modules/ecr"

  repository_name = var.ecr_repository_name
}



module "acm" {
  source = "../../modules/acm"

  domain_name               = var.domain_name
  subject_alternative_names = ["*.${var.domain_name}"]
  tags = {
    Environment = "dev"
    Project     = "ecommerce-platform"
    ManagedBy   = "terraform"
  }
}

module "addons" {
  source = "../../modules/addons"

  count = var.enable_addons ? 1 : 0

  cluster_name                           = module.eks.cluster_name
  cluster_endpoint                       = module.eks.cluster_endpoint
  cluster_certificate_authority_data     = module.eks.cluster_certificate_authority_data
  load_balancer_controller_irsa_role_arn = module.eks.load_balancer_controller_irsa_role_arn
  region                                 = var.region
  vpc_id                                 = module.vpc.vpc_id
}


