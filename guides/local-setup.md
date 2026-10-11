# Running the Application Locally (Bare-Metal / Developer Mode)

This guide walks you through running the entire **DevOps Shack Polyglot Microservices** platform locally on your machine **without Docker or containers**. Every microservice runs natively using its respective runtime, and all 7 services connect to an isolated PostgreSQL database.

---

## Architecture & Service Map

| Port | Service | Tech Stack | Responsibility | Database |
|:---:|:---|:---|:---|:---|
| **5432** | PostgreSQL | PostgreSQL 16 | Relational data persistence | `auth_db`, `catalog_db`, etc. |
| **8081** | Auth Service | Java 21 + Spring Boot | User registration, JWT login, session | `auth_db` |
| **8082** | Catalog Service | Go 1.22+ | Product catalog, pricing, search | `catalog_db` |
| **8083** | Inventory Service | Node.js 20+ + Express | Stock levels, inventory reservations | `inventory_db` |
| **8084** | Order Service | Python 3.11+ + FastAPI | Checkout lifecycle, orchestration | `order_db` |
| **8085** | Payment Service | C# + ASP.NET Core 8.0 | Mock payment capture & refunds | `payment_db` |
| **8086** | Notification Service | Ruby 3.2+ + Sinatra | Event notifications, user inbox | `notification_db` |
| **8087** | Analytics Service | PHP 8.2+ CLI | Metrics aggregation, snapshots | `analytics_db` |
| **5173** | Frontend Web UI | React 18 + Vite + Tailwind | Responsive user interface | *N/A* |

---

## 1. Prerequisites Installation

### Ubuntu / Debian / WSL2

Run the following commands to install all required compilers, runtimes, and tools:

```bash
sudo apt update

# Core tools, PostgreSQL, Java 21, Go, Python, Ruby, PHP
sudo apt install -y \
  postgresql postgresql-contrib \
  openjdk-21-jdk maven \
  golang-go \
  python3 python3-venv python3-pip \
  ruby-full build-essential libpq-dev \
  php-cli php-pgsql php-curl \
  curl git

# Install Node.js 22 LTS
curl -fsSL https://deb.nodesource.com/setup_22.x | sudo -E bash -
sudo apt install -y nodejs

# Install .NET 8 SDK
sudo apt install -y dotnet-sdk-8.0
```

> **Note for macOS users**: You can install the equivalent tools via Homebrew:
> `brew install postgresql@16 openjdk@21 maven go node python@3.11 dotnet-sdk ruby php`

---

## 2. PostgreSQL Database Setup

1. **Start the PostgreSQL Service**:
   ```bash
   sudo systemctl enable --now postgresql
   ```

2. **Run the Database Bootstrap Script**:
   The script creates the dedicated database user `microapp` (password: `microapp123`) and initializes 7 independent databases:
   ```bash
   cd ~/ecommerce
   sudo -u postgres psql -f ./database/bootstrap.sql
   ```

3. **Verify Database Creation**:
   ```bash
   sudo -u postgres psql -c "\l" | grep -E "auth_db|catalog_db|inventory_db|order_db|payment_db|notification_db|analytics_db"
   ```

---

## 3. Quick Start (All Services with Helper Scripts)

The repository includes pre-configured automation scripts in `scripts/`:

### Start All Services
```bash
cd ~/ecommerce
./scripts/start-all.sh
```
This script will:
- Check required runtime dependencies.
- Compile or install packages for each service.
- Launch all 7 microservices and the Vite frontend as background processes.
- Output process PIDs and log files to `logs/`.

### Check Health of All Services
```bash
./scripts/health-check.sh
```
You should see `UP` / `OK` for all 7 backend services and the frontend.

### Stop All Services
```bash
./scripts/stop-all.sh
```

---

## 4. Running Each Service Individually (Manual Developer Mode)

If you are developing or debugging a specific service, you can run it in a dedicated terminal window:

### 1. Auth Service (Java / Spring Boot)
```bash
cd ~/ecommerce/services/auth-service
export AUTH_DB_URL="jdbc:postgresql://localhost:5432/auth_db"
export DB_USER="microapp"
export DB_PASSWORD="microapp123"

mvn spring-boot:run
```
*Health Check*: `curl http://localhost:8081/actuator/health`

---

### 2. Catalog Service (Go)
```bash
cd ~/ecommerce/services/catalog-service
export CATALOG_DB_DSN="postgres://microapp:microapp123@localhost:5432/catalog_db?sslmode=disable"
export PORT="8082"

go run .
```
*Health Check*: `curl http://localhost:8082/health`

---

### 3. Inventory Service (Node.js)
```bash
cd ~/ecommerce/services/inventory-service
export INVENTORY_DB_URL="postgres://microapp:microapp123@localhost:5432/inventory_db"
export PORT="8083"

npm install
npm start
```
*Health Check*: `curl http://localhost:8083/health`

---

### 4. Order Service (Python / FastAPI)
```bash
cd ~/ecommerce/services/order-service
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

export ORDER_DB_URL="postgresql://microapp:microapp123@localhost:5432/order_db"
export CATALOG_SERVICE_URL="http://localhost:8082"
export INVENTORY_SERVICE_URL="http://localhost:8083"
export NOTIFICATION_SERVICE_URL="http://localhost:8086"

uvicorn main:app --host 0.0.0.0 --port 8084 --reload
```
*Health Check*: `curl http://localhost:8084/health`

---

### 5. Payment Service (C# / .NET 8)
```bash
cd ~/ecommerce/services/payment-service
export ConnectionStrings__DefaultConnection="Host=localhost;Port=5432;Database=payment_db;Username=microapp;Password=microapp123"
export ORDER_SERVICE_URL="http://localhost:8084"
export NOTIFICATION_SERVICE_URL="http://localhost:8086"

dotnet run --urls "http://0.0.0.0:8085"
```
*Health Check*: `curl http://localhost:8085/health`

---

### 6. Notification Service (Ruby / Sinatra)
```bash
cd ~/ecommerce/services/notification-service
export NOTIFICATION_DB_URL="postgres://microapp:microapp123@localhost:5432/notification_db"
export PORT="8086"

bundle install
bundle exec ruby app.rb -o 0.0.0.0 -p 8086
```
*Health Check*: `curl http://localhost:8086/health`

---

### 7. Analytics Service (PHP)
```bash
cd ~/ecommerce/services/analytics-service
export ANALYTICS_DB_URL="postgres://microapp:microapp123@localhost:5432/analytics_db"
export CATALOG_SERVICE_URL="http://localhost:8082"
export INVENTORY_SERVICE_URL="http://localhost:8083"
export ORDER_SERVICE_URL="http://localhost:8084"
export PAYMENT_SERVICE_URL="http://localhost:8085"

php -S 0.0.0.0:8087 -t .
```
*Health Check*: `curl http://localhost:8087/health`

---

### 8. Frontend Web UI (React + Vite)
```bash
cd ~/ecommerce/frontend
npm install
npm run dev -- --host 0.0.0.0 --port 5173
```
Open your browser at: **`http://localhost:5173`**

---

## 5. Testing & Verification

### Demo Admin Credentials
- **Email**: `admin@devopsshack.com`
- **Password**: `admin123`

### Complete End-to-End Test Flow
1. Open `http://localhost:5173` in your browser.
2. Log in with the demo admin credentials.
3. Browse products in the **Catalog** tab.
4. Add items to cart and click **Checkout** (triggers Order & Inventory reservation).
5. Navigate to Orders, click **Pay** (triggers Payment simulation & Notification).
6. Check the **Notifications** tab to verify order confirmation and payment receipts.
7. Open the **Analytics** tab to view real-time revenue and order snapshots.

---

## 6. Troubleshooting

- **Port Conflict (`Address already in use`)**:
  Check which process is listening on the port and terminate it:
  ```bash
  sudo lsof -i :8081  # Replace with the affected port
  ```
- **PostgreSQL Connection Refused**:
  Ensure PostgreSQL is active:
  ```bash
  sudo systemctl status postgresql
  ```
- **Ruby Bundler Permission Errors**:
  Configure Bundler to install gems in user directory:
  ```bash
  bundle config set --local path 'vendor/bundle'
  ```
- **Logs Inspection**:
  When using `start-all.sh`, check the service log file under `logs/<service-name>.log`.
