# eCommerce Platform Grafana Dashboards

This directory contains declarative Grafana dashboards and Kubernetes ConfigMap definitions for the **Polyglot eCommerce Platform** microservices on AWS EKS.

---

## 1. Dashboards Overview

All dashboards are grouped under the **`eCommerce Platform`** folder in Grafana:

| Dashboard | UID | Description | Primary Data Sources |
|---|---|---|---|
| **eCommerce Platform - Application Overview** | `ecommerce-overview` | High-level executive & SRE dashboard with service health cards, aggregate CPU/memory/network KPIs, dedicated databases PVC storage utilization, and centralized log ingestion rates. | Prometheus, Loki |
| **eCommerce Microservices - Deep Dive & Performance** | `ecommerce-services` | In-depth service-level analysis. Includes dynamic dropdown selectors for service and pod instances, CPU vs request/limit, memory working set, CGroup CPU throttling seconds, and active pod placement table. | Prometheus |
| **eCommerce Centralized Logs & Traces Explorer** | `ecommerce-logs` | Operational troubleshooting dashboard for container logs and traces. Features keyword search, log-level filtering, error & warning rates over time, live log stream, and correlation with Grafana Tempo traces via `trace_id`. | Loki, Tempo |

---

## 2. Accessing in Grafana

1. Start `kubectl port-forward`:
   ```bash
   kubectl port-forward -n monitoring svc/kube-prometheus-stack-grafana 3000:80
   ```
2. Open **`http://localhost:3000`** in your browser.
3. Login credentials:
   - **Username**: `admin`
   - **Password**: `admin123`
4. Navigate to **Dashboards > eCommerce Platform**. Direct links:
   - **Overview**: `http://localhost:3000/d/ecommerce-overview/ecommerce-platform-application-overview`
   - **Deep Dive**: `http://localhost:3000/d/ecommerce-services/ecommerce-microservices-deep-dive-and-performance`
   - **Logs & Traces**: `http://localhost:3000/d/ecommerce-logs/ecommerce-centralized-logs-and-traces-explorer`

---

## 3. GitOps & Declarative Provisioning

The dashboards are provisioned as Kubernetes ConfigMaps with the label `grafana_dashboard: "1"` in the `monitoring` namespace. The `kube-prometheus-stack` sidecar automatically watches and reloads them.

To re-apply or update the ConfigMaps:
```bash
kubectl apply -f monitoring/dashboards/ecommerce-dashboards-configmap.yaml
```

To regenerate the JSON files from code:
```bash
python3 monitoring/dashboards/generate_dashboards.py
```

