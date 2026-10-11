# Full-Stack Observability Guide (Prometheus, Grafana, Loki, Tempo & OpenTelemetry)

This guide documents the full-stack observability architecture added to the **Terraform Addons module** (`terraform/modules/addons/observability.tf`). It provides metrics, centralized logging, distributed tracing, and unified telemetry collection across the polyglot microservices platform.

---

## 1. Observability Architecture & Telemetry Pipeline

```text
+-----------------------------------------------------------------------------------+
|                            Polyglot Microservices                                 |
|  (Auth, Catalog, Inventory, Order, Payment, Notification, Analytics, Frontend)    |
+-----------------------------------------+-----------------------------------------+
                                          |
                      Traces, Metrics, Logs (OTLP gRPC/HTTP :4317 / :4318)
                                          v
+-----------------------------------------------------------------------------------+
|                        OpenTelemetry Collector (Gateway)                          |
|  - Ingestion: OTLP gRPC (:4317), OTLP HTTP (:4318)                                |
|  - Processing: Memory Limiter, Batching, Resource Attribution                     |
+--------------------+--------------------+--------------------+--------------------+
                     |                    |                    |
            Traces   |           Metrics  |             Logs   |
                     v                    v                    v
              +------------+       +------------+       +------------+
              |   Tempo    |       | Prometheus |       |    Loki    |
              |  (Traces)  |       | (Metrics)  |       |   (Logs)   |
              +-----+------+       +-----+------+       +-----+------+
                    |                    |                    |
                    +--------------------+--------------------+
                                         |
                                         v
                         +-------------------------------+
                         |          Grafana UI           |
                         |  - Pre-linked DataSources     |
                         |  - Trace-to-Logs Navigation   |
                         |  - Trace-to-Metrics Analysis  |
                         +-------------------------------+
```

---

## 2. Stack Components & Responsibilities

| Component | Technology | Helm Chart | Responsibility | Storage & Persistence |
|---|---|---|---|---|
| **Prometheus** | Prometheus Operator | `kube-prometheus-stack` | Collects, stores, and evaluates infrastructure and service metrics | `20Gi` gp3 (15d retention) |
| **Grafana** | Grafana 11+ | `kube-prometheus-stack` | Visual dashboards, unified exploratory UI, alert visualization | `10Gi` gp3 |
| **Loki** | Grafana Loki | `grafana/loki` | Horizontal, scalable log aggregation for container stdout/stderr | `20Gi` gp3 |
| **Promtail** | Grafana Promtail | `grafana/promtail` | Kubernetes Node DaemonSet shipping pod logs to Loki | Stateless DaemonSet |
| **Tempo** | Grafana Tempo | `grafana/tempo` | High-volume distributed tracing backend (OTLP, Jaeger, Zipkin) | `20Gi` gp3 (72h retention) |
| **OpenTelemetry** | OTel Collector | `open-telemetry/opentelemetry-collector` | Central pipeline receiving, batching, and routing telemetry | Stateless Deployment |

---

## 3. How to Enable in Terraform

The observability stack is defined in `terraform/modules/addons/observability.tf` and wired into `terraform/environments/dev/`.

By default, the addon flags are set to `false` so current infrastructure is not modified. When you are ready to provision the stack:

### Step 1: Enable Addons in `terraform.tfvars`
In `terraform/environments/dev/terraform.tfvars` (or command line variables):
```hcl
enable_addons        = true
enable_observability = true
```

### Step 2: Customize Component Variables (Optional)
The following variables in `terraform/modules/addons/variables.tf` can be adjusted:

```hcl
observability_namespace             = "monitoring"
observability_storage_class         = "gp3"
enable_prometheus                   = true
enable_grafana                      = true
enable_loki                         = true
enable_tempo                        = true
enable_opentelemetry                = true
prometheus_storage_size             = "20Gi"
grafana_admin_password              = "admin123"
loki_storage_size                   = "20Gi"
tempo_storage_size                  = "20Gi"
```

### Step 3: Apply with Terraform
```bash
cd ~/ecommerce/terraform/environments/dev
terraform init
terraform plan -out=tfplan
terraform apply tfplan
```

---

## 4. Internal Cluster Endpoints

Once deployed, the following internal CoreDNS endpoints will be available to all microservices in the cluster:

| Service | Internal Cluster URL | Port / Protocol |
|---|---|---|
| **OpenTelemetry OTLP gRPC** | `opentelemetry-collector.monitoring.svc.cluster.local:4317` | gRPC |
| **OpenTelemetry OTLP HTTP** | `http://opentelemetry-collector.monitoring.svc.cluster.local:4318` | HTTP |
| **Prometheus Server** | `http://kube-prometheus-stack-prometheus.monitoring.svc.cluster.local:9090` | HTTP |
| **Grafana UI** | `http://kube-prometheus-stack-grafana.monitoring.svc.cluster.local:80` | HTTP |
| **Loki Log Push** | `http://loki.monitoring.svc.cluster.local:3100/loki/api/v1/push` | HTTP |
| **Tempo OTLP gRPC** | `tempo.monitoring.svc.cluster.local:4317` | gRPC |

---

## 5. Accessing the Grafana Dashboard

### Access via Kubectl Port-Forward
```bash
kubectl port-forward -n monitoring svc/kube-prometheus-stack-grafana 3000:80
```
Open **`http://localhost:3000`** in your browser.

- **Username**: `admin`
- **Password**: `admin123` *(or the value configured in `grafana_admin_password`)*

---

## 6. Pre-Configured 360° Observability Correlation

The Terraform configuration automatically configures Grafana with cross-telemetry links:

1. **Logs to Traces (Loki → Tempo)**:
   - Any log entry in Loki containing `trace_id=<id>` automatically renders a clickable link directly opening the corresponding trace waterfall in Tempo.
2. **Traces to Logs (Tempo → Loki)**:
   - When inspecting a trace span in Tempo, a **"Logs for this span"** button queries Loki filtering by `app`, `service.name`, and the exact span timeframe.
3. **Traces to Metrics (Tempo → Prometheus)**:
   - From any trace view, click **"Metrics"** to view real-time request rates and latencies in Prometheus for the targeted microservice.

---

## 7. Instrumenting Microservices with OpenTelemetry

To send traces and metrics from the microservices to the OpenTelemetry Collector, configure the standard OTLP environment variables in their deployment specs or Helm values:

```yaml
env:
  - name: OTEL_EXPORTER_OTLP_ENDPOINT
    value: "http://opentelemetry-collector.monitoring.svc.cluster.local:4317"
  - name: OTEL_EXPORTER_OTLP_PROTOCOL
    value: "grpc"
  - name: OTEL_SERVICE_NAME
    value: "order-service" # (Use the service's name)
```

