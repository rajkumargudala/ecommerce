output "cluster_arn" {
  description = "Amazon MSK cluster ARN."
  value       = aws_msk_cluster.this.arn
}

output "bootstrap_brokers_sasl_scram" {
  description = "Bootstrap broker connection string for TLS and SASL/SCRAM clients."
  value       = aws_msk_cluster.this.bootstrap_brokers_sasl_scram
}

output "scram_secret_arn" {
  description = "Secrets Manager ARN containing the MSK SCRAM username and password."
  value       = aws_secretsmanager_secret.scram.arn
}

output "secret_reader_role_arn" {
  description = "IRSA role ARN for the Kafka client service account."
  value       = aws_iam_role.client.arn
}
