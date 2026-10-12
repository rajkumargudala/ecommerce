# Dedicated Database per Microservice (Database-per-Service Architecture)

In this production-ready architecture, each microservice operates with its own **dedicated, isolated PostgreSQL database**. This guarantees fault domain isolation, prevents cascading database failures, allows independent scaling, and secures sensitive customer and order records behind service-specific credentials.

---

## 1. Dedicated Databases Overview

| Microservice | Technology | Dedicated DB Service | Database Name | Dedicated Username | Init Script | Storage (gp3) |
|---|---|---|---|---|---|---|
| **Auth Service** | Java 21 / Spring Boot | `auth-db:5432` | `auth_db` | `auth_user` | `auth-db-init.sql` | `5Gi` |
| **Catalog Service** | Go 1.22 | `catalog-db:5432` | `catalog_db` | `catalog_user` | `catalog-db-init.sql` | `5Gi` |
| **Inventory Service** | Node.js 20 | `inventory-db:5432` | `inventory_db` | `inventory_user` | `inventory-db-init.sql` | `5Gi` |
| **Order Service** | Python 3.11 / FastAPI | `order-db:5432` | `order_db` | `order_user` | `order-db-init.sql` | `5Gi` |
| **Payment Service** | C# / .NET 8 | `payment-db:5432` | `payment_db` | `payment_user` | `payment-db-init.sql` | `5Gi` |
| **Notification Service** | Ruby 3.2 / Sinatra | `notification-db:5432` | `notification_db` | `notification_user` | `notification-db-init.sql` | `5Gi` |
| **Analytics Service** | PHP 8.2 | `analytics-db:5432` | `analytics_db` | `analytics_user` | `analytics-db-init.sql` | `5Gi` |

---

## 2. Kubernetes & EKS Provisioning

Each dedicated database is deployed on AWS EKS via **Helm** as a dedicated `StatefulSet`:
- Managed PersistentVolumeClaims dynamically provisioned with AWS EBS `gp3` storage class.
- Passwords and usernames are stored in dedicated Kubernetes Secrets (`<service>-db-secret`).
- Individual ClusterIP services (`auth-db`, `catalog-db`, etc.) isolate network access within the cluster.
- External databases (e.g. AWS RDS PostgreSQL instances) can be connected by simply configuring `database.enabled: false` and providing `database.host: <rds-endpoint>` in `helm/ecommerce/values.yaml`.

