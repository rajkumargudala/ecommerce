# EKS cluster via the community module. Pod Identity is used for AWS workload
# credentials because this account's Organizations policy denies OIDC provider
# creation. The control-plane and node IAM roles come from the iam module.

module "eks" {
  source  = "terraform-aws-modules/eks/aws"
  version = "~> 20.24"

  cluster_name    = var.cluster_name
  cluster_version = var.cluster_version

  cluster_endpoint_public_access           = false
  cluster_endpoint_private_access          = true
  enable_cluster_creator_admin_permissions = true
  authentication_mode                      = "API_AND_CONFIG_MAP"
  enable_irsa                              = false

  vpc_id     = var.vpc_id
  subnet_ids = var.private_subnet_ids

  # Reuse the control-plane role created by the iam module.
  create_iam_role = false
  iam_role_arn    = var.cluster_role_arn

  eks_managed_node_group_defaults = {
    ami_type = "AL2023_x86_64_STANDARD"
  }

  # Replace the module's unrestricted default egress with VPC-only traffic
  # plus HTTPS to the S3 gateway endpoint used for ECR image layers.
  node_security_group_enable_recommended_rules = false
  node_security_group_additional_rules = {
    ingress_nodes_and_pods = {
      description = "Node and pod traffic within the VPC"
      protocol    = "-1"
      from_port   = 0
      to_port     = 0
      type        = "ingress"
      self        = true
    }
    egress_vpc = {
      description = "Cluster and pod traffic within the VPC"
      protocol    = "-1"
      from_port   = 0
      to_port     = 0
      type        = "egress"
      cidr_blocks = [var.vpc_cidr]
    }
    egress_s3 = {
      description     = "HTTPS to S3 for ECR image layers"
      protocol        = "tcp"
      from_port       = 443
      to_port         = 443
      type            = "egress"
      prefix_list_ids = [var.s3_prefix_list_id]
    }
  }

  eks_managed_node_groups = {
    default = {
      min_size       = var.node_min_size
      max_size       = var.node_max_size
      desired_size   = var.node_desired_size
      instance_types = var.node_instance_types
      capacity_type  = "ON_DEMAND"

      # Reuse the node role created by the iam module.
      create_iam_role = false
      iam_role_arn    = var.node_role_arn
    }
  }

  cluster_addons = {
    coredns                = {}
    kube-proxy             = {}
    vpc-cni                = {}
    eks-pod-identity-agent = {}
  }

  tags = var.tags
}

# ---------------------------------------------------------------------------
# EBS CSI driver — the managed add-on that lets PVCs provision EBS volumes.
# It uses EKS Pod Identity, so no cluster OIDC provider is required.
# ---------------------------------------------------------------------------
data "aws_caller_identity" "current" {}

data "aws_iam_policy_document" "ebs_csi_assume" {
  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRole", "sts:TagSession"]

    principals {
      type        = "Service"
      identifiers = ["pods.eks.amazonaws.com"]
    }

    condition {
      test     = "StringEquals"
      variable = "aws:SourceAccount"
      values   = [data.aws_caller_identity.current.account_id]
    }

    condition {
      test     = "StringEquals"
      variable = "aws:RequestTag/kubernetes-namespace"
      values   = ["kube-system"]
    }

    condition {
      test     = "StringEquals"
      variable = "aws:RequestTag/kubernetes-service-account"
      values   = ["ebs-csi-controller-sa"]
    }
  }
}

resource "aws_iam_role" "ebs_csi" {
  name               = "${var.cluster_name}-ebs-csi-irsa"
  assume_role_policy = data.aws_iam_policy_document.ebs_csi_assume.json
  tags               = var.tags
}

resource "aws_iam_role_policy_attachment" "ebs_csi" {
  role       = aws_iam_role.ebs_csi.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonEBSCSIDriverPolicy"
}

resource "aws_eks_addon" "ebs_csi" {
  cluster_name                = module.eks.cluster_name
  addon_name                  = "aws-ebs-csi-driver"
  resolve_conflicts_on_create = "OVERWRITE"
  resolve_conflicts_on_update = "OVERWRITE"
  tags                        = var.tags

  pod_identity_association {
    role_arn        = aws_iam_role.ebs_csi.arn
    service_account = "ebs-csi-controller-sa"
  }

  # Needs nodes to schedule the controller/daemonset onto.
  depends_on = [module.eks, aws_iam_role_policy_attachment.ebs_csi]
}

# ---------------------------------------------------------------------------
# AWS Load Balancer Controller — IAM policy and IRSA role
# ---------------------------------------------------------------------------
resource "aws_iam_policy" "load_balancer_controller" {
  name        = "${var.cluster_name}-AWSLoadBalancerControllerIAMPolicy"
  description = "IAM policy for AWS Load Balancer Controller on ${var.cluster_name}"
  policy      = file("${path.module}/policies/aws_load_balancer_controller.json")
  tags        = var.tags
}

data "aws_iam_policy_document" "load_balancer_controller_assume" {
  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRole", "sts:TagSession"]

    principals {
      type        = "Service"
      identifiers = ["pods.eks.amazonaws.com"]
    }

    condition {
      test     = "StringEquals"
      variable = "aws:SourceAccount"
      values   = [data.aws_caller_identity.current.account_id]
    }

    condition {
      test     = "StringEquals"
      variable = "aws:RequestTag/kubernetes-namespace"
      values   = ["kube-system"]
    }

    condition {
      test     = "StringEquals"
      variable = "aws:RequestTag/kubernetes-service-account"
      values   = ["aws-load-balancer-controller"]
    }
  }
}

resource "aws_iam_role" "load_balancer_controller" {
  name               = "${var.cluster_name}-aws-load-balancer-controller-irsa"
  assume_role_policy = data.aws_iam_policy_document.load_balancer_controller_assume.json
  tags               = var.tags
}

resource "aws_iam_role_policy_attachment" "load_balancer_controller" {
  role       = aws_iam_role.load_balancer_controller.name
  policy_arn = aws_iam_policy.load_balancer_controller.arn
}

resource "aws_eks_pod_identity_association" "load_balancer_controller" {
  cluster_name    = module.eks.cluster_name
  namespace       = "kube-system"
  role_arn        = aws_iam_role.load_balancer_controller.arn
  service_account = "aws-load-balancer-controller"
  tags            = var.tags

  # The association requires the agent add-on and a role with permissions.
  depends_on = [module.eks, aws_iam_role_policy_attachment.load_balancer_controller]
}

