# Running the Application Traditionally with Raw Kubernetes Manifests

This guide walks you through deploying the **DevOps Shack Polyglot Microservices** platform to a Kubernetes cluster (such as AWS EKS, Minikube, or Kind) using **traditional raw YAML manifests** located in the `k8s/` directory.

---

## Manifest Directory Structure

The repository organizes manifests into clean, service-specific subdirectories under `k8s/` along with a root `kustomization.yaml`:

```text
k8s/
├── kustomization.yaml             # Kustomize manifest aggregating all services
├── postgres/
│   ├── configmap.yaml             # Database bootstrap SQL script
│   ├── service.yaml               # ClusterIP headless service for PostgreSQL
│   └── statefulset.yaml           # StatefulSet with 10Gi PersistentVolumeClaim
├── auth/
│   ├── deployment.yaml            # Java Spring Boot Deployment
│   └── service.yaml               # ClusterIP Service (Port 8081)
├── catalog/
│   ├── deployment.yaml            # Go Catalog Deployment
│   └── service.yaml               # ClusterIP Service (Port 8082)
├── inventory/
│   ├── deployment.yaml            # Node.js Inventory Deployment
│   └── service.yaml               # ClusterIP Service (Port 8083)
├── order/
│   ├── deployment.yaml            # Python FastAPI Order Deployment
│   └── service.yaml               # ClusterIP Service (Port 8084)
├── payment/
│   ├── deployment.yaml            # C# .NET Payment Deployment
│   └── service.yaml               # ClusterIP Service (Port 8085)
├── notification/
│   ├── deployment.yaml            # Ruby Sinatra Notification Deployment
│   └── service.yaml               # ClusterIP Service (Port 8086)
├── analytics/
│   ├── deployment.yaml            # PHP Analytics Deployment
│   └── service.yaml               # ClusterIP Service (Port 8087)
└── frontend/
    ├── deployment.yaml            # React Web UI Deployment
    ├── service.yaml               # ClusterIP Service (Port 5173)
    └── ingress.yaml               # ALB Ingress resource
```

---

## 1. Prerequisites

1. **Kubernetes Cluster**: An active Kubernetes cluster (v1.28+) such as AWS EKS, Minikube, or Kind.
2. **Kubectl**: Configured to communicate with your target cluster:
   ```bash
   kubectl cluster-info
   ```
3. **StorageClass Provider**:
   - For **AWS EKS**: The AWS EBS CSI driver addon must be active, with a `gp3` or `gp2` StorageClass configured.
   - For **Minikube / Kind**: Standard `standard` or `local-path` storage class is automatically provided.
4. **Ingress Controller**:
   - For **AWS EKS**: AWS Load Balancer Controller installed in `kube-system`.
   - For **Minikube**: `minikube addons enable ingress`.

---

## 2. Deployment Method 1: One-Click Kustomize (Recommended)

Because all services are defined in `k8s/kustomization.yaml`, you can apply the entire infrastructure with a single command:

```bash
cd ~/ecommerce
kubectl apply -k k8s/
```

This command deploys the PostgreSQL ConfigMap, StatefulSet, all 7 microservice Deployments and Services, the Frontend, and the Ingress resource in the correct dependency graph.

---

## 3. Deployment Method 2: Sequential Step-by-Step

If you prefer to deploy and verify each tier sequentially:

### Step 1: Deploy Database Tier (PostgreSQL)
```bash
# 1. Apply PostgreSQL init script ConfigMap
kubectl apply -f k8s/postgres/configmap.yaml

# 2. Apply Headless Service
kubectl apply -f k8s/postgres/service.yaml

# 3. Apply StatefulSet (requests 10Gi Persistent Volume)
kubectl apply -f k8s/postgres/statefulset.yaml

# 4. Wait for PostgreSQL pod to reach Ready status
kubectl wait --for=condition=ready pod -l app=postgres --timeout=120s
```

### Step 2: Deploy Core Backend Microservices
```bash
# Auth Service (Java)
kubectl apply -f k8s/auth/

# Catalog Service (Go)
kubectl apply -f k8s/catalog/

# Inventory Service (Node.js)
kubectl apply -f k8s/inventory/

# Order Service (Python)
kubectl apply -f k8s/order/

# Payment Service (C# .NET)
kubectl apply -f k8s/payment/

# Notification Service (Ruby)
kubectl apply -f k8s/notification/

# Analytics Service (PHP)
kubectl apply -f k8s/analytics/
```

### Step 3: Deploy Frontend & Ingress
```bash
# Frontend Web UI
kubectl apply -f k8s/frontend/deployment.yaml
kubectl apply -f k8s/frontend/service.yaml

# Ingress Route (creates AWS Application Load Balancer on EKS)
kubectl apply -f k8s/frontend/ingress.yaml
```

---

## 4. Verification & Status Checks

### Check Pod Status
Verify that all 9 pods are `Running` and ready:
```bash
kubectl get pods -o wide
```
Expected output:
```text
NAME                                   READY   STATUS    RESTARTS   AGE
analytics-service-59df5f6cc7-gslnz     1/1     Running   0          5m
auth-service-55b4b66677-zngcv          1/1     Running   0          5m
catalog-service-759b77795f-8cjsd       1/1     Running   0          5m
frontend-bfd749cf8-mdv8k               1/1     Running   0          5m
inventory-service-7b68dbfd67-75bs9     1/1     Running   0          5m
notification-service-b9f99b949-ltlvm   1/1     Running   0          5m
order-service-c84cfbb47-ppj75          1/1     Running   0          5m
payment-service-8f4c46d5-9rv8p         1/1     Running   0          5m
postgres-0                             1/1     Running   0          5m
```

### Check Storage & Persistent Volume Claims
```bash
kubectl get pvc
```
Expected output:
```text
NAME                       STATUS   VOLUME                                     CAPACITY   ACCESS MODES   STORAGECLASS   AGE
postgres-data-postgres-0   Bound    pvc-c4d23186-79b6-466b-b0ab-381b5c83484a   10Gi       RWO            gp3            5m
```

### Check Internal Services
```bash
kubectl get svc
```

### Check Ingress & Inbound URL
```bash
kubectl get ingress ecommerce-ingress
```
On AWS EKS, copy the `ADDRESS` field (e.g. `k8s-default-ecommerc-*.us-east-1.elb.amazonaws.com`).

---

## 5. Accessing the Application

### Option A: Via AWS Application Load Balancer (EKS)
Open the external Ingress ALB URL in your browser:
```
http://<ALB-INGRESS-ADDRESS>/
```

### Option B: Via Kubectl Port Forward (Local / Minikube)
If running locally without an ALB:
```bash
kubectl port-forward svc/frontend 5173:5173
```
Then access `http://localhost:5173` in your browser.

- **Demo Admin Email**: `admin@devopsshack.com`
- **Demo Password**: `admin123`

---

## 6. Important Operational Notes & Troubleshooting

### StatefulSet Immutability Rule
In Kubernetes, `spec.volumeClaimTemplates` in a `StatefulSet` cannot be modified via `kubectl apply` once created. If you need to update its storage class or template specs without downtime or data loss:
```bash
# Delete only the controller metadata; keep pod and PVC data intact
kubectl delete statefulset postgres --cascade=orphan

# Re-apply updated manifest
kubectl apply -f k8s/postgres/statefulset.yaml
```

### Internal Microservice DNS Resolution
Within the Kubernetes cluster, services discover each other using CoreDNS service names:
- PostgreSQL: `postgres:5432`
- Catalog Service: `catalog-service:8082`
- Order Service: `order-service:8084`
- Inventory Service: `inventory-service:8083`

---

## 7. Teardown & Clean Up

To delete all deployed resources:
```bash
kubectl delete -k k8s/
```
> **Note**: Deleting the StatefulSet will retain the PVC `postgres-data-postgres-0` to protect your data. If you wish to permanently delete the volume:
> `kubectl delete pvc postgres-data-postgres-0`
