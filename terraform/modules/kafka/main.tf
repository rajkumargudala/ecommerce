locals {
  topic_configuration = <<-PROPERTIES
    auto.create.topics.enable=true
    default.replication.factor=${var.broker_count}
    min.insync.replicas=${var.broker_count - 1}
    num.partitions=3
  PROPERTIES
}

resource "aws_kms_key" "scram" {
  description         = "Encrypts the Amazon MSK SCRAM credential secret for ${var.name}."
  enable_key_rotation = true
  tags                = var.tags
}

resource "aws_kms_alias" "scram" {
  name          = "alias/${var.name}-scram"
  target_key_id = aws_kms_key.scram.key_id
}

resource "random_password" "scram" {
  length  = 48
  special = false
}

resource "aws_secretsmanager_secret" "scram" {
  name                    = "AmazonMSK_${var.name}"
  description             = "SASL/SCRAM credentials for ${var.name}."
  kms_key_id              = aws_kms_key.scram.arn
  recovery_window_in_days = 7
  tags                    = var.tags
}

resource "aws_secretsmanager_secret_version" "scram" {
  secret_id = aws_secretsmanager_secret.scram.id
  secret_string = jsonencode({
    username = "ecommerce_app"
    password = random_password.scram.result
  })
}

resource "aws_cloudwatch_log_group" "brokers" {
  name              = "/aws/msk/${var.name}/brokers"
  retention_in_days = 14
  tags              = var.tags
}

resource "aws_security_group" "brokers" {
  name        = "${var.name}-brokers"
  description = "Allow Kafka TLS/SASL clients from EKS worker nodes."
  vpc_id      = var.vpc_id
  tags        = merge(var.tags, { Name = "${var.name}-brokers" })

  ingress {
    description     = "MSK SASL/SCRAM over TLS from EKS worker nodes."
    from_port       = 9096
    to_port         = 9096
    protocol        = "tcp"
    security_groups = [var.client_security_group_id]
  }

  egress {
    description = "Broker communication and AWS service endpoints."
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_msk_configuration" "this" {
  name              = "${var.name}-configuration"
  kafka_versions    = [var.kafka_version]
  server_properties = local.topic_configuration
}

resource "aws_msk_cluster" "this" {
  cluster_name           = var.name
  kafka_version          = var.kafka_version
  number_of_broker_nodes = var.broker_count

  broker_node_group_info {
    instance_type   = var.broker_instance_type
    client_subnets  = var.private_subnet_ids
    security_groups = [aws_security_group.brokers.id]

    storage_info {
      ebs_storage_info {
        volume_size = var.broker_storage_gib
      }
    }
  }

  client_authentication {
    sasl {
      scram {
        enabled = true
      }
    }
  }

  encryption_info {
    encryption_in_transit {
      client_broker = "TLS"
      in_cluster    = true
    }
  }

  configuration_info {
    arn      = aws_msk_configuration.this.arn
    revision = aws_msk_configuration.this.latest_revision
  }

  logging_info {
    broker_logs {
      cloudwatch_logs {
        enabled   = true
        log_group = aws_cloudwatch_log_group.brokers.name
      }
    }
  }

  tags = var.tags

  depends_on = [aws_secretsmanager_secret_version.scram]
}

resource "aws_msk_scram_secret_association" "this" {
  cluster_arn     = aws_msk_cluster.this.arn
  secret_arn_list = [aws_secretsmanager_secret.scram.arn]
}

data "aws_iam_policy_document" "client_assume" {
  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRoleWithWebIdentity"]

    principals {
      type        = "Federated"
      identifiers = [var.oidc_provider_arn]
    }

    condition {
      test     = "StringEquals"
      variable = "${var.oidc_provider}:aud"
      values   = ["sts.amazonaws.com"]
    }

    condition {
      test     = "StringEquals"
      variable = "${var.oidc_provider}:sub"
      values   = ["system:serviceaccount:${var.namespace}:${var.service_account_name}"]
    }
  }
}

resource "aws_iam_role" "client" {
  name               = "${var.name}-secret-reader"
  assume_role_policy = data.aws_iam_policy_document.client_assume.json
  tags               = var.tags
}

data "aws_iam_policy_document" "client_secret_read" {
  statement {
    sid       = "ReadKafkaCredentials"
    effect    = "Allow"
    actions   = ["secretsmanager:DescribeSecret", "secretsmanager:GetSecretValue"]
    resources = [aws_secretsmanager_secret.scram.arn]
  }

  statement {
    sid       = "DecryptKafkaCredentialsThroughSecretsManager"
    effect    = "Allow"
    actions   = ["kms:Decrypt"]
    resources = [aws_kms_key.scram.arn]

    condition {
      test     = "StringEquals"
      variable = "kms:ViaService"
      values   = ["secretsmanager.${var.region}.amazonaws.com"]
    }

    condition {
      test     = "StringEquals"
      variable = "kms:EncryptionContext:SecretARN"
      values   = [aws_secretsmanager_secret.scram.arn]
    }
  }
}

resource "aws_iam_role_policy" "client_secret_read" {
  name   = "${var.name}-read-scram-secret"
  role   = aws_iam_role.client.id
  policy = data.aws_iam_policy_document.client_secret_read.json
}
