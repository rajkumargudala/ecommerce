# Multi-stage build for Go Catalog Service
FROM golang:1.26-alpine AS builder

WORKDIR /app

# Download dependencies
COPY go.mod go.sum ./
RUN go mod download

# Copy source code and build statically linked binary
COPY . .
RUN CGO_ENABLED=0 GOOS=linux go build -ldflags="-w -s" -o catalog-service .

# Runtime stage
FROM alpine:3.24

WORKDIR /app

# Install CA certificates and create non-root user
RUN apk upgrade --no-cache \
    && apk add --no-cache ca-certificates \
    && addgroup -S appgroup && adduser -S appuser -G appgroup
USER appuser

# Copy compiled binary from builder
COPY --from=builder /app/catalog-service .

EXPOSE 8082

ENTRYPOINT ["./catalog-service"]
