# Running the Application with Docker & Docker Compose

This guide explains how to build, run, and manage the entire **DevOps Shack Polyglot Microservices** platform using **Docker** and **Docker Compose**. Containerization ensures that you do not need to install any of the 7 language compilers or PostgreSQL on your host system.

---

## Container Architecture & Port Map

The application stack consists of **9 coordinated containers** running on an isolated Docker bridge network (`polyglot-network`):

| Container Name | Service | Technology Stack | Host Port | Internal Port | Healthcheck |
|---|---|---|---|---|---|
| `polyglot-postgres` | PostgreSQL Database | PostgreSQL 16 Alpine | `5432` | `5432` | `pg_isready -U postgres` |
| `auth-service` | Auth Service | Java 21 / Spring Boot | `8081` | `8081` | HTTP `/actuator/health` |
| `catalog-service` | Catalog Service | Go 1.22+ | `8082` | `8082` | HTTP `/health` |
| `inventory-service` | Inventory Service | Node.js 20+ / Express | `8083` | `8083` | HTTP `/health` |
| `order-service` | Order Service | Python 3.11 / FastAPI | `8084` | `8084` | HTTP `/health` |
| `payment-service` | Payment Service | C# / ASP.NET Core 8.0 | `8085` | `8085` | HTTP `/health` |
| `notification-service` | Notification Service | Ruby 3.2 / Sinatra | `8086` | `8086` | HTTP `/health` |
| `analytics-service` | Analytics Service | PHP 8.2 CLI | `8087` | `8087` | HTTP `/health` |
| `frontend` | Frontend Web UI | React 18 + Vite | `5173` | `5173` | TCP port listener |

---

## 1. Prerequisites

- **Docker Engine**: Version 24.0 or higher
- **Docker Compose**: Version 2.20 or higher
- Verify your installation:
  ```bash
  docker --version
  docker compose version
  ```

---

## 2. Multi-Stage Dockerfiles Overview

Each microservice utilizes an optimized multi-stage `Dockerfile` to minimize image size and ensure high build efficiency:

- **Auth Service** (`services/auth-service/Dockerfile`):
  Uses Maven with Eclipse Temurin JDK 21 to compile the JAR, then packages it into a lightweight Temurin JRE runtime image.
- **Catalog Service** (`services/catalog-service/Dockerfile`):
  Uses Go 1.22 Alpine to compile a statically linked binary, producing an ultra-small production container.
- **Payment Service** (`services/payment-service/Dockerfile`):
  Uses .NET 8 SDK to build and publish the C# binary, running on the official ASP.NET Core 8 runtime image.
- **Order Service** (`services/order-service/Dockerfile`):
  Uses Python 3.11 slim image with `pip install --no-cache-dir`.
- **Database** (`postgres:16-alpine`):
  Mounts `./database/bootstrap.sql` into `/docker-entrypoint-initdb.d/01-bootstrap.sql` so all 7 microservice databases are created automatically when the container boots.

---

## 3. Quick Start (Build & Run)

### Step 1: Clone the Repository
```bash
git clone https://github.com/rajkumargudala/ecommerce.git
cd ecommerce
```

### Step 2: Build All Container Images
Build all images concurrently:
```bash
docker compose build
```

### Step 3: Launch the Stack in the Background
```bash
docker compose up -d
```
Docker Compose will start `polyglot-postgres` first, wait for the database healthcheck to pass, and then launch all 7 backend microservices and the React frontend.

### Step 4: Check Container Status
```bash
docker compose ps
```
You should see all 9 containers with status `Up` (or `Up (healthy)`):
```text
NAME                   IMAGE                         COMMAND                  SERVICE                STATUS
auth-service           ecommerce-auth-service        "java -jar app.jar"      auth-service           Up (healthy)
catalog-service        ecommerce-catalog-service     "./main"                 catalog-service        Up (healthy)
frontend               ecommerce-frontend            "npm run dev ..."        frontend               Up
inventory-service      ecommerce-inventory-service   "npm start"              inventory-service      Up (healthy)
notification-service   ecommerce-notification        "bundle exec ruby ..."   notification-service   Up (healthy)
order-service          ecommerce-order-service       "uvicorn main:app ..."   order-service          Up (healthy)
payment-service        ecommerce-payment-service     "dotnet Payment.dll"     payment-service        Up (healthy)
polyglot-postgres      postgres:16-alpine            "docker-entrypoint..."   postgres               Up (healthy)
```

---

## 4. Verification & Health Checks

### Check Backend Service Endpoints
Run these `curl` commands to verify that every service is responding:

```bash
# Auth Service
curl -s http://localhost:8081/actuator/health | grep UP

# Catalog Service
curl -s http://localhost:8082/health

# Inventory Service
curl -s http://localhost:8083/health

# Order Service
curl -s http://localhost:8084/health

# Payment Service
curl -s http://localhost:8085/health

# Notification Service
curl -s http://localhost:8086/health

# Analytics Service
curl -s http://localhost:8087/health
```

### Access Web UI
Open your browser and navigate to:
```
http://localhost:5173
```
- **Admin Email**: `admin@devopsshack.com`
- **Password**: `admin123`

---

## 5. Inspecting Logs & Debugging

### Tail Logs for All Services
```bash
docker compose logs -f
```

### Tail Logs for a Specific Service
```bash
docker compose logs -f order-service
docker compose logs -f auth-service
```

### Open a Shell Inside a Running Container
```bash
# Check postgres databases
docker compose exec postgres psql -U postgres -c "\l"

# Shell into Python order-service
docker compose exec order-service /bin/sh

# Shell into Go catalog-service
docker compose exec catalog-service /bin/sh
```

---

## 6. Managing Persistent Data

The database uses a named Docker volume `postgres-data`:

- **Restarting without losing data**:
  ```bash
  docker compose down
  docker compose up -d
  ```
  All database records (products, orders, users, payments) will be preserved.

- **Complete Reset (Wipe Database and Re-initialize)**:
  ```bash
  docker compose down -v
  docker compose up -d --build
  ```
  The `-v` flag removes the named volume, forcing PostgreSQL to re-run `01-bootstrap.sql` on the next boot.

---

## 7. Rebuilding a Single Service

When making code changes to a single microservice, you don't need to restart everything:

```bash
# Example: rebuild and recreate only the order-service
docker compose up -d --no-deps --build order-service
```
