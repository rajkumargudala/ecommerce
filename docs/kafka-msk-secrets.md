# Kafka and AWS Secrets Manager

The order service publishes `order.created` records to Amazon MSK. It first writes
each event to a PostgreSQL outbox in the same transaction as the order, then a
background dispatcher publishes it. The notification worker consumes the topic
and inserts notifications idempotently into `notification-db`.

Both Kafka clients use SASL/SCRAM-SHA-512 over TLS. Terraform creates the MSK
cluster, the `AmazonMSK_` Secrets Manager credential, a customer-managed KMS key,
the EKS IRSA role, and the network rule that permits EKS workers to reach the
brokers. The application pods use the `ecommerce-kafka-client` service account;
the Python clients call Secrets Manager at runtime through the AWS SDK. The
password is not passed through Helm values or Kubernetes environment variables.

## Provision MSK

From the repository root, use the existing Terraform backend and deploy the dev
environment. The defaults create three `kafka.t3.small` brokers across the
private subnets:

```bash
terraform -chdir=terraform/environments/dev init
terraform -chdir=terraform/environments/dev plan
terraform -chdir=terraform/environments/dev apply
```

Terraform generates the SCRAM password and stores its value in Secrets Manager.
Keep the Terraform state protected because it contains the generated secret
value. The outputs below expose only the broker list, secret ARN, and IAM role
ARN:

```bash
terraform -chdir=terraform/environments/dev output -raw kafka_bootstrap_brokers_sasl_scram
terraform -chdir=terraform/environments/dev output -raw kafka_scram_secret_arn
terraform -chdir=terraform/environments/dev output -raw kafka_secret_reader_role_arn
```

## Enable Kafka in Helm values

Set the outputs in the deployment values file; these values are identifiers and
endpoints, not the Kafka password:

```yaml
order:
  tag: order-service-<version-1.0.4-commit-sha>
kafka:
  enabled: true
  bootstrapServers: "<kafka_bootstrap_brokers_sasl_scram output>"
  secretArn: "<kafka_scram_secret_arn output>"
  secretReaderRoleArn: "<kafka_secret_reader_role_arn output>"
  awsRegion: us-east-1
  ordersTopic: orders.created
  consumerGroupId: notification-service
  notificationWorker:
    tag: kafka-notification-worker-<version-1.0.4-commit-sha>
```

Use image tags from the version-1.0.4 build for both services. The chart creates
the annotated service account and configures the order service and notification
worker. Apply the same chart templates and values to
the GitOps repository branch used by Argo CD before syncing the application;
the Argo CD manifest in this repository currently points at the separate
`ecommerce-gitops` repository.

When `kafka.enabled` is false, the order service keeps its existing HTTP call to
the notification service. When enabled, that call is replaced by the Kafka
event path.
