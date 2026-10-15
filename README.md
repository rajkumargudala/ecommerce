# Polyglot eCommerce Microservices Platform (AWS EKS & GitOps)

An enterprise, cloud-native eCommerce platform built using **seven distinct programming languages** and deployed exclusively to **Amazon EKS** using **Helm** and **ArgoCD (GitOps)**. The underlying AWS infrastructure is provisioned and managed via **Terraform**.

---

## 🌟 Architecture Highlights

- **Exclusively EKS-Native**: All local, manual, and Docker Compose deployments have been eliminated in favor of production-ready Kubernetes deployments managed via Helm and ArgoCD.
- **Database-per-Service**: Every microservice operates with its own dedicated, isolated PostgreSQL StatefulSet database with dedicated credentials, storage, and health checks:
  - `auth-db` (Auth Service - Java Spring Boot)
  - `catalog-db` (Catalog Service - Go)
  - `inventory-db` (Inventory Service - Node.js)
  - `order-db` (Order Service - Python)
  - `payment-db` (Payment Service - C# .NET)
  - `notification-db` (Notification Service - Ruby)
  - `analytics-db` (Analytics Service - PHP)
- **Automated GitOps Continuous Delivery**:
  - Code pushed to `master` triggers `.github/workflows/ci.yml`.
  - Images are built in parallel and published to Amazon ECR.
  - Image tags in `rajkumargudala/ecommerce-gitops` (`helm/values.yaml` on `main`) are auto-updated.
  - ArgoCD reconciles the cluster to the desired state.
- **Modernized Enterprise UI**:
  - Redesigned with a modern design system (dark slate & vibrant accents).
  - Global slide-out Cart Drawer accessible anywhere.
  - Interactive Cluster & Dedicated Database Topology Monitor.
  - Multi-stage Order Lifecycle Stepper (`Created ➔ Paid ➔ Processing ➔ Shipped`).
  - Real-time stock health visualization and batch restocking.
- **Infrastructure as Code**:
  - Complete AWS foundation maintained in `terraform/` (VPC, IAM, EKS, ECR, ACM, Addons).

---

## 📂 Repository Structure

```text
├── .github/
│   └── workflows/
│       └── ci.yml               # Automated CI: Chart lint, parallel image builds, GitOps tag updates
├── argocd/
│   └── application.yaml         # ArgoCD Application resource with automated sync and prune
├── database/                    # Dedicated initialization scripts & schema documentation
│   ├── auth-db-init.sql
│   ├── catalog-db-init.sql
│   ├── inventory-db-init.sql
│   ├── order-db-init.sql
│   ├── payment-db-init.sql
│   ├── notification-db-init.sql
│   ├── analytics-db-init.sql
│   └── README.md
├── frontend/                    # Modern React 19 + Vite + Nginx UI
│   ├── src/
│   │   ├── App.jsx              # Enterprise Control Center UI
│   │   ├── styles.css           # Modern design tokens and styling
│   │   └── api.js               # API client
│   ├── nginx.conf               # Nginx reverse proxy routing /api/* to microservices
│   └── Dockerfile               # Multi-stage production container build
├── guides/
│   ├── cicd-helm-argocd.md      # Comprehensive GitOps, Helm, and ArgoCD guide
│   └── observability-setup.md   # Prometheus, Grafana, Loki, Tempo & OpenTelemetry
├── helm/
│   └── ecommerce/               # Production Helm v2.0 chart
│       ├── Chart.yaml
│       ├── values.yaml          # Centralized configuration with dedicated DB blocks
│       └── templates/
│           ├── databases-secrets.yaml      # Kubernetes Secrets for dedicated DBs
│           ├── databases-services.yaml     # ClusterIP services for dedicated DBs
│           ├── databases-statefulsets.yaml # StatefulSets with gp3 PVCs for dedicated DBs
│           ├── pdb.yaml                    # PodDisruptionBudgets
│           ├── frontend-ingress.yaml       # AWS ALB Ingress
│           └── <service>-deployment.yaml   # Service deployments with rolling updates
├── scripts/
│   └── health-check.sh          # EKS ingress and microservice health check script
├── services/                    # 7 Polyglot Microservices
│   ├── auth-service/            # Java 21 / Spring Boot
│   ├── catalog-service/         # Go 1.22
│   ├── inventory-service/       # Node.js 20 / Express
│   ├── order-service/           # Python 3.11 / FastAPI
│   ├── payment-service/         # C# / ASP.NET Core 8
│   ├── notification-service/    # Ruby 3.2 / Sinatra
│   └── analytics-service/       # PHP 8.2
├── terraform/                   # AWS Infrastructure Foundation
│   ├── environments/dev/        # Dev environment entry point
│   └── modules/                 # Reusable modules (VPC, IAM, EKS, ECR, ACM, Addons)
└── ARCHITECTURE.md              # Detailed architecture documentation
```

---

## 🚀 Deployment Instructions

### 1. Provision Infrastructure via Terraform

```bash
cd terraform/environments/dev
terraform init
terraform plan
terraform apply
```

### 2. Connect to EKS Cluster

```bash
aws eks update-kubeconfig --region us-east-1 --name ecommerce-cluster-dev
kubectl get nodes
```

### 3. Deploy via ArgoCD (GitOps)

Apply the ArgoCD application manifest:

```bash
kubectl apply -f argocd/application.yaml
```

ArgoCD will automatically pull the Helm chart from `helm/ecommerce`, render the manifests, and deploy the entire platform onto your EKS cluster.

### 4. Direct Helm Deployment (Alternative CLI Mode)

```bash
helm lint helm/ecommerce
helm upgrade --install ecommerce-platform helm/ecommerce -n default --create-namespace
```

### 5. Verify Health

Run the automated health verification script against your ingress endpoint:

```bash
./scripts/health-check.sh http://<YOUR-ALB-INGRESS-HOSTNAME>
```

