# Running Lumaire with CI/CD, Helm and Argo CD

This guide describes the GitHub Actions pipeline for the Lumaire eCommerce application and its GitOps promotion flow.

The pipeline validates the Helm chart, waits for SonarQube quality gates, scans code and images with Trivy, builds all application images, and publishes uniquely tagged images to **Amazon ECR**. A push to either publishing branch opens a pull request to its matching branch in the GitOps repository. Each PR contains the image tags and the frontend Deployment and Service templates from the same source commit; it preserves GitOps-specific values and other workload templates. Argo CD deploys after the PR is reviewed and merged when its target revision points to that branch.

---

## 1. End-to-End Architecture & GitOps Flow

```text
+---------------------+
|   Pull Request / Push | (Targets or pushes to 'main' or 'version-1.0.4')
+----------+----------+
           |
           v
+---------------------+
|   GitHub Actions    |  .github/workflows/ci.yml
|                     |  1. Lint and render the Helm chart
|   CI Pipeline       |  2. Enforce SonarQube quality gates and Trivy scans
|                     |  3. Build, scan and create SBOMs for 14 images
|                     |  4. Publish immutable run-specific tags on trusted branch pushes
|                     |  5. Open a branch-matched GitOps promotion PR
+----------+----------+
           |
           v
+---------------------+
|   GitOps Repository | (rajkumargudala/ecommerce-gitops, chart in helm/)
+----------+----------+
           |
           | Merge of reviewed promotion PR
           v
+---------------------+
|   ArgoCD (GitOps)   |  argocd/application.yaml
|                     |  1. Detects merged image tag updates
| Continuous Delivery |  2. Renders Helm template dynamically
|                     |  3. Reconciles live EKS cluster state
+----------+----------+
           |
           v
+--------------------------------------------------------------+
|                        AWS EKS Cluster                       |
|  - Ingress: AWS Application Load Balancer                    |
|  - Pods: 12 backend services + frontend (RollingUpdate)      |
|  - Databases: 12 dedicated PostgreSQL 16 instances            |
+--------------------------------------------------------------+
```

---

## 2. Helm Chart Architecture (`helm/ecommerce`)

The application is packaged into a production-ready Helm chart located at [`helm/ecommerce/`](../helm/ecommerce):

```text
helm/ecommerce/
├── Chart.yaml                  # Chart metadata and version (v2.0.0)
├── values.yaml                 # Centralized configuration (images, tags, ports, dedicated DBs, resources)
└── templates/
    ├── _helpers.tpl            # Standardized Kubernetes labeling helpers
    ├── frontend-ingress.yaml   # AWS ALB Ingress template
    ├── frontend-service.yaml   # Frontend ClusterIP service
    ├── frontend-deployment.yaml # Frontend Web UI Deployment
    ├── databases-secrets.yaml  # Dedicated Kubernetes Secrets for all 12 service databases
    ├── databases-services.yaml # Dedicated ClusterIP services for all 12 databases
    ├── databases-statefulsets.yaml # Dedicated StatefulSets with gp3 PVCs for all 12 databases
    ├── pdb.yaml                # PodDisruptionBudgets for high-availability workloads
    └── additional-services.yaml (cart, shipping, reviews, promotions, and search)
```

### Key Parameters in `values.yaml`

| Value Key | Default Value | Description |
|---|---|---|
| `global.imageRegistry` | `877013879278.dkr.ecr.us-east-1.amazonaws.com` | Central container registry |
| `global.imageRepository` | `ecommerce-platform` | Repository prefix for all services |
| `databaseDefaults.storageClassName` | `gp3` | EBS CSI driver StorageClass for all dedicated DBs |
| `databaseDefaults.storageSize` | `5Gi` | Default storage per dedicated database instance |
| `<service>.database.enabled` | `true` | Provisions dedicated `<service>-db` StatefulSet and Service |
| `<service>.database.host` | `<service>-db` | Dedicated database hostname (or external RDS endpoint) |
| `podDisruptionBudget.enabled` | `true` | Enforces minimum available pods during cluster maintenance |
| `frontend.ingress.enabled` | `true` | Enables AWS ALB Ingress |

---

## 3. GitHub Actions CI/CD Pipeline (`.github/workflows/ci.yml`)

The workflow runs chart validation, SonarQube analysis, Trivy filesystem scanning, and a 14-image build-and-scan matrix. The auth service runs Maven `verify`; other services currently have no unit or integration test suites wired into CI. Trivy blocks HIGH and CRITICAL vulnerability, secret, and configuration findings. Each image is scanned before publishing, and a CycloneDX SBOM is uploaded as a workflow artifact for 30 days. The GitOps promotion job lints and renders its updated chart before opening a PR. Deployments use `maxSurge: 0` and `maxUnavailable: 1`, matching the successful recovery from pod-IP exhaustion; this avoids extra pods during rollout. A single-replica optional service may be briefly unavailable while it is replaced.

ECR tags include the service name, commit SHA, workflow run ID, and retry attempt. ECR is configured to reject tag overwrites. Pull requests and manual runs build and scan without publishing. Pushes to `version-1.0.4` publish to ECR and open or update a promotion PR targeting `gitops-release-1.0.4`. Pushes to `main` publish and open or update a separate promotion PR targeting GitOps `main`.

SonarQube is configured with the display projects **Lumaire** and **Lumaire Payment Service**, using stable keys `ecommerce-platform` and `ecommerce-platform-payment-service`. Fork and Dependabot pull requests skip SonarQube because they do not receive repository secrets. Require the `CI gate` status check on protected source branches.

### GitHub Actions configuration

Create the `production` environment with required reviewers and restrict it to `main`. Create a `release` environment restricted to `version-1.0.4`; reviewers are optional there. Configure the following repository variables and secrets:

| Name | Type | Value |
|---|---|---|
| `AWS_ROLE_ARN` | Variable | AWS IAM role ARN trusted for this repository's `main` and `version-1.0.4` refs via GitHub OIDC |
| `SONAR_HOST_URL` | Variable | SonarQube Server URL |
| `SONAR_TOKEN` | Secret | Token with analysis access to both SonarQube project keys |
| `GITOPS_TOKEN` | Secret | Fine-grained token with Contents and Pull requests read/write access to `rajkumargudala/ecommerce-gitops` |

See [the CI security setup](../docs/ci-security-setup.md) for the OIDC trust and ECR permission policies. Remove old AWS access-key secrets after OIDC publishing is configured.

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

Argo CD continuously monitors the separate `rajkumargudala/ecommerce-gitops` repository and ensures the cluster matches its `helm/` chart and environment values. The checked-in Application tracks `gitops-release-1.0.4`.

### Step 1: Deploy ArgoCD on EKS (if not already installed)
```bash
# Create argocd namespace
kubectl create namespace argocd

# Install ArgoCD via Helm
helm repo add argo https://argoproj.github.io/argo-helm
helm repo update
helm upgrade --install argocd argo/argo-cd \
  --namespace argocd \
  --set server.service.type=ClusterIP
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
    repoURL: https://github.com/rajkumargudala/ecommerce-gitops.git
    targetRevision: gitops-release-1.0.4
    path: helm/
    helm:
      valueFiles:
        - values.yaml
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

Apply the application manifest from this repository:
```bash
kubectl apply -f ~/ecommerce/argocd/application.yaml
```

### Step 3: Access the ArgoCD Web UI
Argo CD uses an internal `ClusterIP` service so Terraform teardown does not leave a Kubernetes load balancer waiting for cleanup. Forward its service port to localhost:
```bash
kubectl port-forward -n argocd svc/argocd-server 8080:80
```
Open `http://localhost:8080` while the port-forward is running.

Retrieve the initial `admin` password:
```bash
kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d && echo
```

Log in to the ArgoCD dashboard with:
- **Username**: `admin`
- **Password**: *(The decrypted password above)*

---

## 6. Verification & Day-2 Operations

After a source branch push, wait for the matching promotion pull request, review the chart and values diff, and merge it. `version-1.0.4` promotes to GitOps `gitops-release-1.0.4`; `main` promotes to GitOps `main`. The checked-in Application follows the release branch.

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
- **Via Git (Recommended GitOps Way)**: Revert the merged GitOps promotion commit in a pull request, then merge it after review. Argo CD will reconcile the previous image tags from the reverted revision.
- **Via ArgoCD UI**: Open the application in the ArgoCD dashboard, click **History and Rollback**, select the desired revision, and click **Rollback**.
