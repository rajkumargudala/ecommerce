# Terraform infrastructure

This Terraform configuration provisions the AWS foundation and cluster add-ons for the eCommerce platform. The active environment is `environments/dev` and uses the `ap-southeast-2` AWS region.

## What Terraform creates

| Area | Resources |
| --- | --- |
| Terraform state | An S3 backend at `ecommerce-bucket-623174465382-ap-southeast-2-an`, key `dev/networking.tfstate`, with S3 lock-file locking. The bucket must already exist. |
| Network | A VPC, public and private subnets across three availability zones, internet gateway, route tables, one NAT gateway, and its Elastic IP. |
| IAM | EKS cluster and worker-node roles and policies, plus workload roles for the EBS CSI driver and AWS Load Balancer Controller. EKS Pod Identity is used for these workloads. |
| Kubernetes | An EKS cluster and managed node group, CoreDNS, kube-proxy, VPC CNI, the Pod Identity agent, the EBS CSI driver, and the `gp3` StorageClass. |
| Container images | The `ecommerce-platform` ECR repository in account `623174465382`, region `ap-southeast-2`, with image scanning, a lifecycle policy, and cross-account publishing access for the CI account. |
| TLS and DNS | An ACM certificate for `learnwithmedevops.online` and `*.learnwithmedevops.online`, with DNS validation records in the existing Route 53 hosted zone. |
| Cluster add-ons | AWS Load Balancer Controller and Argo CD. Argo CD's server Service is configured as a Kubernetes `LoadBalancer`. |
| Observability | Prometheus, Grafana, Loki, Promtail, Tempo, and the OpenTelemetry Collector in the `monitoring` namespace. Persistent volumes use the `gp3` StorageClass. |

The application itself is deployed separately through the Argo CD application manifest at `../argocd/application.yaml`; Terraform installs Argo CD but does not apply that application manifest.

## Apply the dev environment

From the repository root:

```bash
cd terraform/environments/dev
terraform init
terraform plan
terraform apply
```

The configured S3 backend stores shared state. Use this environment directory for Terraform commands so Terraform reads the correct backend and state.

The GitHub Actions CI role is in AWS account `877013879278` by default (`ecr_ci_account_id`). Terraform grants that account push access to this ECR repository. Keep this value aligned with `ECR_CI_ACCOUNT_ID` in `.github/workflows/ci.yml`. CI publishes to `623174465382.dkr.ecr.ap-southeast-2.amazonaws.com/ecommerce-platform`; the GitOps promotion workflow also writes that registry into its Helm values so Argo CD keeps deploying from the same repository.

## Connect to the EKS cluster

Configure `kubectl` with the AWS credentials for an IAM principal that has access to the cluster:

```bash
aws eks update-kubeconfig --region ap-southeast-2 --name ecommerce-cluster-dev
kubectl get nodes
```

Check that the add-ons are ready:

```bash
kubectl get pods -n monitoring
kubectl get pods -n argocd
```

## Grafana

Grafana is a cluster-internal service, so use a port forward from your workstation:

```bash
kubectl -n monitoring port-forward svc/kube-prometheus-stack-grafana 3000:80
```

Open <http://localhost:3000>. Sign in as `admin`. Retrieve the configured password from its Kubernetes Secret:

```bash
kubectl -n monitoring get secret kube-prometheus-stack-grafana \
  -o jsonpath='{.data.admin-password}' | base64 --decode
echo
```

The current Terraform module default is `admin123` (`grafana_admin_password` in `modules/addons/variables.tf`); the Secret command above returns the value actually configured in the cluster. Change the default before using this setup beyond a development environment, and do not commit a real password to source control.

Grafana is configured with Prometheus, Loki, and Tempo data sources. Use Grafana's **Explore** view to query metrics, logs, and traces.

## Prometheus

Prometheus has no separate login configured and is not exposed through a public load balancer. Port-forward it locally:

```bash
kubectl -n monitoring port-forward svc/kube-prometheus-stack-prometheus 9090:9090
```

Open <http://localhost:9090>. Its in-cluster service URL is `http://kube-prometheus-stack-prometheus.monitoring.svc.cluster.local:9090`.

## Argo CD

The Argo CD server Service is configured as a load balancer. Get its AWS load balancer hostname:

```bash
kubectl -n argocd get svc argocd-server
```

Open `http://<EXTERNAL-IP-or-hostname>` in a browser. The Helm configuration starts the server with `--insecure`, so it serves HTTP at this endpoint. For workstation-only access, port-forward instead:

```bash
kubectl -n argocd port-forward svc/argocd-server 8080:80
```

Then open <http://localhost:8080>.

The initial username is `admin`. Read the initial password from the Kubernetes Secret:

```bash
kubectl -n argocd get secret argocd-initial-admin-secret \
  -o jsonpath='{.data.password}' | base64 --decode
echo
```

This Secret is for the initial login and may be removed after the password is changed. Keep the new password in your approved secrets manager.

To check the Argo CD applications after applying the repository manifest:

```bash
kubectl get applications -n argocd
```

## Logs, traces, and telemetry endpoints

Loki and Tempo are internal services without authentication configured. They are pre-wired as Grafana data sources. To access their HTTP endpoints locally, use:

```bash
kubectl -n monitoring port-forward svc/loki 3100:3100
```

Open another terminal for Tempo:

```bash
kubectl -n monitoring port-forward svc/tempo 3200:3100
```

Loki's readiness endpoint is `http://localhost:3100/ready`; Tempo's is `http://localhost:3200/ready`. The OpenTelemetry Collector accepts OTLP gRPC on port `4317` and OTLP HTTP on port `4318` inside the cluster. Its in-cluster gRPC endpoint is `opentelemetry-collector.monitoring.svc.cluster.local:4317`.

## Useful Terraform outputs

From `terraform/environments/dev`, list outputs or print individual service URLs:

```bash
terraform output
terraform output -raw cluster_name
terraform output -raw observability_grafana_url
terraform output -raw observability_prometheus_url
terraform output -raw observability_loki_url
```

The Grafana and Prometheus Terraform URLs are cluster-internal DNS names; use the port-forward commands above to open them from your workstation.

## Cost and cleanup

The EKS cluster, worker nodes, NAT gateway, load balancers, and EBS volumes incur AWS charges while they exist. Review `terraform plan` before changes. When the dev environment is no longer needed, `terraform destroy` removes Terraform-managed resources and the data stored on their persistent volumes.
