# Running the Application with CI/CD Tools & Helm (GitOps with ArgoCD)

This guide provides an end-to-end walkthrough of the enterprise **GitOps delivery pipeline** for the **DevOps Shack Polyglot Microservices** platform. 

The pipeline automates chart validation, parallel multi-language container builds, image pushes to **Amazon ECR**, automated Git manifest tag updates via **GitHub Actions**, and continuous reconciliation onto **AWS EKS** via **ArgoCD** and **Helm**.

---

## 1. End-to-End Architecture & GitOps Flow

```text
+---------------------+
|   Developer Push    | (Pushes feature/bugfix to 'main' branch)
+----------+----------+
           |
           v
+---------------------+
|   GitHub Actions    |  .github/workflows/ci.yml
|                     |  1. Lint & Validate Helm Chart (helm lint & template)
|   CI Pipeline       |  2. Build & Push 8 Docker Images in parallel to Amazon ECR
|                     |  3. Update image tags in helm/ecommerce/values.yaml
|                     |  4. Auto-commit & push updated values to Git [skip ci]
+----------+----------+
           |
           v
+---------------------+
|   Git Repository    | (Contains desired state in helm/ecommerce/)
+----------+----------+
           |
           | Polling / Webhook
           v
+---------------------+
|   ArgoCD (GitOps)   |  argocd/application.yaml
|                     |  1. Detects new Git commit with updated image tags
| Continuous Delivery |  2. Renders Helm template dynamically
|                     |  3. Reconciles live EKS cluster state
+----------+----------+
           |
           v
+--------------------------------------------------------------+
|                        AWS EKS Cluster                       |
|  - Ingress: AWS Application Load Balancer                    |
|  - Pods: 8 microservices (RollingUpdate) + PostgreSQL 16     |
+--------------------------------------------------------------+
```

---

## 2. Helm Chart Architecture (`helm/ecommerce`)

The application is packaged into a production-ready Helm chart located at [`helm/ecommerce/`](../helm/ecommerce):

```text
helm/ecommerce/
├── Chart.yaml                  # Chart metadata and version (v1.0.0)
├── values.yaml                 # Centralized configuration (images, tags, ports, resources)
└── templates/
    ├── _helpers.tpl            # Standardized Kubernetes labeling helpers
    ├── frontend-ingress.yaml   # AWS ALB Ingress template
    ├── postgres-configmap.yaml # Database initialization script ConfigMap
    ├── postgres-service.yaml   # Postgres headless ClusterIP service
    ├── postgres-statefulset.yaml # Postgres StatefulSet with gp3 volume claim
    └── <service>-deployment.yaml / <service>-service.yaml (for all 8 services)
```

### Key Parameters in `values.yaml`

| Value Key | Default Value | Description |
|---|---|---|
| `global.environment` | `dev` | Deployment environment name |
| `global.ecrRegistry` | `877013879278.dkr.ecr.us-east-1.amazonaws.com` | Central container registry |
| `postgres.storage.size` | `10Gi` | Persistent disk allocation for PostgreSQL |
| `postgres.storage.storageClassName` | `gp3` | EBS CSI driver StorageClass |
| `ingress.enabled` | `true` | Enables AWS ALB Ingress |
| `ingress.alb.scheme` | `internet-facing` | Provision public Application Load Balancer |

---

## 3. GitHub Actions CI/CD Pipeline (`.github/workflows/ci.yml`)

The workflow consists of three automated stages:

### Stage 1: `validate-chart`
Runs `helm lint helm/ecommerce` and `helm template` to prevent invalid templates or indentation errors from reaching the repository.

### Stage 2: `build-and-push` (Matrix Strategy)
Compiles and builds Docker images in parallel for all 8 microservices using Docker Buildx and GitHub Actions cache:
- `auth-service` (Java 21 / Maven)
- `catalog-service` (Go)
- `inventory-service` (Node.js)
- `order-service` (Python)
- `payment-service` (C# .NET)
- `notification-service` (Ruby)
- `analytics-service` (PHP)
- `frontend` (React Vite)

Images are pushed to ECR tagged with both `:latest` and `:<service>-<GIT_SHA>`.

### Stage 3: `update-git-manifests` (GitOps Automated Tagging)
Extracts the commit SHA (`${{ github.sha }}`), updates `helm/ecommerce/values.yaml` using `sed`, and commits the updated tags back to `main` with `[skip ci]`.

### Required GitHub Repository Secrets
To enable the workflow, configure the following secrets under **Settings > Secrets and variables > Actions**:

| Secret Name | Value Description |
|---|---|
| `AWS_ACCESS_KEY_ID` | AWS IAM Access Key with ECR push permissions |
| `AWS_SECRET_ACCESS_KEY` | AWS IAM Secret Access Key |

---

## 4. Deploying with Helm Manually (CLI Mode)

If you wish to test or deploy the Helm chart directly from your terminal:

### 1. Lint the Chart
```bash
cd ~/ecommerce
helm lint helm/ecommerce
```

### 2. Render and Inspect Templates
```bash
helm template ecommerce-test helm/ecommerce
```

### 3. Install or Upgrade the Release
```bash
helm upgrade --install ecommerce helm/ecommerce \
  --namespace default \
  --create-namespace
```

### 4. Check Helm Release Status
```bash
helm status ecommerce
helm list
```

---

## 5. Continuous Delivery with ArgoCD (GitOps Mode)

ArgoCD continuously monitors the Git repository and ensures the cluster matches the declarative configuration in `helm/ecommerce/`.

### Step 1: Deploy ArgoCD on EKS (if not already installed)
```bash
# Create argocd namespace
kubectl create namespace argocd

# Install ArgoCD via Helm
helm repo add argo https://argoproj.github.io/argo-helm
helm repo update
helm upgrade --install argocd argo/argo-cd \
  --namespace argocd \
  --set server.service.type=LoadBalancer
```

### Step 2: Apply the ArgoCD Application
The repository contains the GitOps application definition at [`argocd/application.yaml`](../argocd/application.yaml):

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: ecommerce-platform
  namespace: argocd
  finalizers:
    - resources-finalizer.argocd.argoproj.io
spec:
  project: default
  source:
    repoURL: https://github.com/rajkumargudala/ecommerce.git
    targetRevision: HEAD
    path: helm/ecommerce
  destination:
    server: https://kubernetes.default.svc
    namespace: default
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
    syncOptions:
      - CreateNamespace=true
```

Apply the application manifest:
```bash
kubectl apply -f ~/ecommerce/argocd/application.yaml
```

### Step 3: Access the ArgoCD Web UI
Retrieve the external Load Balancer URL:
```bash
kubectl get svc -n argocd argocd-server -o jsonpath='{.status.loadBalancer.ingress[0].hostname}'
```

Retrieve the initial `admin` password:
```bash
kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d && echo
```

Log in to the ArgoCD dashboard with:
- **Username**: `admin`
- **Password**: *(The decrypted password above)*

---

## 6. Verification & Day-2 Operations

### Verify Sync Status in CLI
```bash
kubectl get applications.argoproj.io -n argocd
```
Expected output:
```text
NAMESPACE   NAME                 SYNC STATUS   HEALTH STATUS
argocd      ecommerce-platform   Synced        Healthy
```

### Verify Running Pods
```bash
kubectl get pods -l app.kubernetes.io/instance=ecommerce
```

### Trigger a Manual Sync
```bash
kubectl patch application ecommerce-platform -n argocd --type merge -p '{"operation":{"sync":{"revision":"HEAD"}}}'
```

### Handling StatefulSet Upgrades in GitOps
Kubernetes StatefulSets forbid updating `volumeClaimTemplates` in place. If storage specifications are changed in `values.yaml`:
```bash
# Orphan delete removes only the controller metadata without stopping pod or wiping disk:
kubectl delete statefulset postgres --cascade=orphan

# ArgoCD will automatically reconcile and recreate the StatefulSet cleanly:
kubectl patch application ecommerce-platform -n argocd --type merge -p '{"operation":{"sync":{"revision":"HEAD"}}}'
```

### Rollbacks
- **Via Git (Recommended GitOps Way)**: Run `git revert <commit-hash>` and push to `main`. ArgoCD will instantly synchronize the cluster back to the previous image tags.
- **Via ArgoCD UI**: Open the application in the ArgoCD dashboard, click **History and Rollback**, select the desired revision, and click **Rollback**.
