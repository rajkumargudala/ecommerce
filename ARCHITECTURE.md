# Production Architecture: Polyglot Microservices on AWS EKS

This platform is an enterprise-grade, polyglot eCommerce microservices system running on **Amazon Elastic Kubernetes Service (AWS EKS)**, managed via **Helm** and continuously reconciled by **ArgoCD (GitOps)**. The underlying cloud foundation (VPC, Subnets, IAM roles, EKS Cluster, ECR, ACM, and Addons) is provisioned via **Terraform**.

---

## 1. High-Level System Architecture

```text
                                  Internet
                                     │
                                     ▼
                ┌─────────────────────────────────────────┐
                │   AWS Application Load Balancer (ALB)   │
                └────────────────────┬────────────────────┘
                                     │
                                     ▼ (Port 80 / Ingress)
                ┌─────────────────────────────────────────┐
                │       React 19 Frontend + Nginx         │
                │        (SPA + Reverse API Proxy)        │
                └────────────────────┬────────────────────┘
                                     │
         ┌───────────┬───────────────┼───────────────┬───────────┐
         │           │               │               │           │
         ▼           ▼               ▼               ▼           ▼
    ┌─────────┐ ┌─────────┐    ┌───────────┐   ┌───────────┐ ┌──────────┐
    │  Auth   │ │ Catalog │    │ Inventory │   │  Orders   │ │ Payments │
    │ Java 21 │ │ Go 1.22 │    │  Node 20  │   │ Python 3.11││ C# .NET 8│
    │  :8081  │ │  :8082  │    │   :8083   │   │   :8084   │ │  :8085   │
    └────┬────┘ └────┬────┘    └─────┬─────┘   └─────┬─────┘ └────┬─────┘
         │           │               │               │            │
         ▼           ▼               ▼               ▼            ▼
     [auth-db] [catalog-db]   [inventory-db]   [order-db]   [payment-db]
     Postgres    Postgres        Postgres       Postgres      Postgres
      (5Gi)       (5Gi)           (5Gi)          (5Gi)         (5Gi)

                               ┌──────────────────────────┐
                               │   Notifications (Ruby)   │
                               │          :8086           │
                               └────────────┬─────────────┘
                                            │
                                            ▼
                                    [notification-db]
                                     Postgres (5Gi)

                               ┌──────────────────────────┐
                               │     Analytics (PHP)      │
                               │          :8087           │
                               └────────────┬─────────────┘
                                            │
                                            ▼
                                     [analytics-db]
                                     Postgres (5Gi)
```

---

## 2. Dedicated Database per Microservice (Database-per-Service)

In accordance with cloud-native microservice best practices, every service owns its **dedicated, isolated PostgreSQL database**. This guarantees fault domain isolation, prevents cross-domain data coupling, and enables independent scaling and maintenance:

| Microservice | Technology | Dedicated DB Service | Database Name | Dedicated User | Persistent Disk (gp3) |
|---|---|---|---|---|---|
| **Auth Service** | Java 21 / Spring Boot | `auth-db:5432` | `auth_db` | `auth_user` | `5Gi` (StatefulSet) |
| **Catalog Service** | Go 1.22 | `catalog-db:5432` | `catalog_db` | `catalog_user` | `5Gi` (StatefulSet) |
| **Inventory Service** | Node.js 20 / Express | `inventory-db:5432` | `inventory_db` | `inventory_user` | `5Gi` (StatefulSet) |
| **Order Service** | Python 3.11 / FastAPI | `order-db:5432` | `order_db` | `order_user` | `5Gi` (StatefulSet) |
| **Payment Service** | C# / ASP.NET Core 8 | `payment-db:5432` | `payment_db` | `payment_user` | `5Gi` (StatefulSet) |
| **Notification Service** | Ruby 3.2 / Sinatra | `notification-db:5432` | `notification_db` | `notification_user` | `5Gi` (StatefulSet) |
| **Analytics Service** | PHP 8.2 | `analytics-db:5432` | `analytics_db` | `analytics_user` | `5Gi` (StatefulSet) |

### Database Features:
- **Zero Cross-Database Coupling**: Services communicate strictly via REST APIs; direct cross-database queries are physically impossible.
- **Dynamic PersistentVolumeClaims**: Backed by AWS EBS `gp3` CSI driver.
- **Kubernetes Secrets**: Database credentials (`username`, `password`, `connection string`) are securely injected via `<service>-db-secret`.
- **RDS Compatibility**: Can be redirected to external AWS RDS PostgreSQL instances at any time by configuring `<service>.database.enabled: false` and providing `<service>.database.host: <rds-endpoint>` in `helm/ecommerce/values.yaml`.

---

## 3. GitOps Continuous Delivery Flow (ArgoCD & Helm)

```text
Developer Git Push (main)
        │
        ▼
GitHub Actions CI (.github/workflows/ci.yml)
  1. Validates and lints Helm Chart (helm lint & helm template)
  2. Builds and pushes 8 multi-stage Docker images to Amazon ECR in parallel
  3. Updates image tags in helm/ecommerce/values.yaml
  4. Commits updated manifest with [skip ci]
        │
        ▼
Git Repository (Desired State in helm/ecommerce/)
        │
        ▼ (Automated GitOps Reconciliation)
ArgoCD Controller (argocd/application.yaml)
  1. Detects new commit in Git
  2. Renders Helm chart templates dynamically
  3. Reconciles state onto AWS EKS Cluster
        │
        ▼
AWS EKS Cluster
  - RollingUpdate deployments for all 8 microservices
  - High availability via PodDisruptionBudgets (PDB)
  - 7 dedicated PostgreSQL StatefulSets with persistent gp3 storage
  - AWS Application Load Balancer Ingress
```

---

## 4. Terraform AWS Infrastructure Foundation

The underlying cloud infrastructure is maintained in `terraform/`:
- **VPC Module** (`terraform/modules/vpc`): Multi-AZ public and private subnets, NAT Gateway, Route Tables.
- **IAM Module** (`terraform/modules/iam`): EKS cluster and node group IAM roles and policies.
- **EKS Module** (`terraform/modules/eks`): Managed EKS cluster and managed node groups.
- **ECR Module** (`terraform/modules/ecr`): Elastic Container Registry for container images.
- **ACM Module** (`terraform/modules/acm`): AWS Certificate Manager for TLS/SSL certificates.
- **Addons Module** (`terraform/modules/addons`): AWS Load Balancer Controller, EBS CSI driver, ArgoCD, and full-stack observability suite (Prometheus, Grafana, Loki, Tempo, OpenTelemetry).
