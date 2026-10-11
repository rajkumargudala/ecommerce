# Running the Application on AWS EC2 (Single VM Guide)

This guide covers provisioning, configuring, and deploying the complete **DevOps Shack Polyglot Microservices** application on an **AWS EC2 instance** running Ubuntu Linux.

---

## Architecture & Sizing Recommendations

Because this platform consists of **7 distinct language runtimes** (Java Spring Boot, Go, Node.js, Python FastAPI, C# .NET Core, Ruby Sinatra, PHP) plus **PostgreSQL** and the **React Vite UI**, memory sizing is important:

| Resource | Minimum Requirement | Recommended Specification |
|---|---|---|
| **EC2 Instance Type** | `t3.medium` (2 vCPU, 4 GiB RAM) | `t3.large` (2 vCPU, 8 GiB RAM) or `c6i.large` |
| **Operating System** | Ubuntu 22.04 LTS / 24.04 LTS (x86_64) | Ubuntu 24.04 LTS (HVM) |
| **EBS Storage** | 20 GB gp3 | 30 GB gp3 (IOPS: 3000, Throughput: 125 MB/s) |
| **Swap Space** | 2 GB (helps prevent OOM during builds) | 4 GB |

---

## 1. AWS Security Group Configuration

Create or attach a Security Group to your EC2 instance with the following inbound rules:

| Type | Protocol | Port Range | Source | Purpose |
|---|---|---|---|---|
| **SSH** | TCP | `22` | `My IP` / Bastion | Secure SSH remote administration |
| **HTTP** | TCP | `80` | `0.0.0.0/0` | Public Web traffic via Nginx reverse proxy |
| **HTTPS** | TCP | `443` | `0.0.0.0/0` | Secure SSL Web traffic |
| **Custom TCP** *(optional)* | TCP | `5173` | `My IP` / `0.0.0.0/0` | Direct access to Vite React Dev server |
| **Custom TCP** *(optional)* | TCP | `8081 - 8087` | `My IP` | Direct debugging access to microservices |

---

## 2. Initial EC2 Provisioning & Setup

1. **Connect to your EC2 instance via SSH**:
   ```bash
   ssh -i /path/to/your-key.pem ubuntu@<EC2-PUBLIC-IP>
   ```

2. **Update system packages and configure swap**:
   ```bash
   sudo apt update && sudo apt upgrade -y

   # Allocate 4 GB swap to ensure stable builds
   sudo fallocate -l 4G /swapfile
   sudo chmod 600 /swapfile
   sudo mkswap /swapfile
   sudo swapon /swapfile
   echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
   ```

3. **Install Git**:
   ```bash
   sudo apt install -y git curl wget
   ```

4. **Clone the repository**:
   ```bash
   git clone https://github.com/rajkumargudala/ecommerce.git ~/ecommerce
   cd ~/ecommerce
   ```

---

## 3. Deployment Method A: Docker Compose (Recommended)

Using Docker Compose on EC2 is the simplest and most reproducible deployment method because each language runtime, library, and dependency is pre-packaged.

### Step 1: Install Docker Engine and Docker Compose
```bash
# Install Docker prerequisites
sudo apt install -y ca-certificates curl gnupg lsb-release

# Add Docker's official GPG key
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg

# Add Docker repository
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Install Docker Engine & Compose plugin
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Grant ubuntu user docker access
sudo usermod -aG docker ubuntu
newgrp docker
```

### Step 2: Build and Start Containers
```bash
cd ~/ecommerce

# Build all microservice images and launch in background
docker compose up -d --build
```

### Step 3: Verify Container Health
```bash
docker compose ps
```
All 9 containers (`polyglot-postgres`, `auth-service`, `catalog-service`, `inventory-service`, `order-service`, `payment-service`, `notification-service`, `analytics-service`, `frontend`) should show `Up` / `healthy`.

---

## 4. Deployment Method B: Native Systemd (Without Docker)

If you prefer to run services natively on the EC2 host:

1. **Install all language runtimes** as documented in the [Local Setup Guide](local-setup.md#1-prerequisites-installation).
2. **Initialize PostgreSQL**:
   ```bash
   sudo systemctl enable --now postgresql
   sudo -u postgres psql -f ~/ecommerce/database/bootstrap.sql
   ```
3. **Use the startup script or create systemd unit files**:
   ```bash
   cd ~/ecommerce
   ./scripts/start-all.sh
   ```
   To verify health:
   ```bash
   ./scripts/health-check.sh
   ```

---

## 5. Exposing the App with Nginx (Port 80 / 443)

Rather than opening multiple non-standard ports (5173, 8081-8087) to the public internet, use **Nginx** as a reverse proxy on Port 80.

### Step 1: Install Nginx
```bash
sudo apt install -y nginx
sudo systemctl enable --now nginx
```

### Step 2: Configure Reverse Proxy
Create `/etc/nginx/sites-available/ecommerce.conf`:

```nginx
server {
    listen 80;
    server_name _;  # Or your EC2 Public DNS / custom domain

    # Frontend Web UI
    location / {
        proxy_pass http://127.0.0.1:5173;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }

    # Auth Service
    location /api/auth/ {
        proxy_pass http://127.0.0.1:8081/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # Catalog Service
    location /api/catalog/ {
        proxy_pass http://127.0.0.1:8082/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # Inventory Service
    location /api/inventory/ {
        proxy_pass http://127.0.0.1:8083/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # Order Service
    location /api/orders/ {
        proxy_pass http://127.0.0.1:8084/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # Payment Service
    location /api/payments/ {
        proxy_pass http://127.0.0.1:8085/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # Notification Service
    location /api/notifications/ {
        proxy_pass http://127.0.0.1:8086/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # Analytics Service
    location /api/analytics/ {
        proxy_pass http://127.0.0.1:8087/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

Enable the configuration and reload Nginx:
```bash
sudo rm -f /etc/nginx/sites-enabled/default
sudo ln -s /etc/nginx/sites-available/ecommerce.conf /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

---

## 6. Accessing the Application

Open your browser and navigate to:
```
http://<YOUR-EC2-PUBLIC-IP>/
```

### Log in with the Demo Credentials:
- **Email**: `admin@devopsshack.com`
- **Password**: `admin123`

---

## 7. Operational Maintenance & Monitoring

### View Container Logs
```bash
# Follow logs for all services
docker compose logs -f

# Follow logs for a specific service
docker compose logs -f order-service
```

### Check Host Resource Consumption
```bash
# Real-time memory consumption
free -h

# Real-time container resource usage (CPU/RAM)
docker stats
```

### Ensure Auto-Restart on EC2 Reboot
Docker Compose services configured with `restart: unless-stopped` will automatically start upon instance reboot as long as the Docker daemon is enabled:
```bash
sudo systemctl enable docker
```
