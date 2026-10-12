#!/usr/bin/env bash
set -e

REGISTRY="877013879278.dkr.ecr.us-east-1.amazonaws.com"
REPO="ecommerce-platform"
IMAGE_PREFIX="$REGISTRY/$REPO"

GIT_SHA=$(git rev-parse --short HEAD)
echo "Current Git SHA: $GIT_SHA"

echo "Logging in to Amazon ECR..."
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin "$REGISTRY"

declare -A SERVICES=(
  ["frontend"]="frontend"
  ["auth-service"]="services/auth-service"
  ["catalog-service"]="services/catalog-service"
  ["inventory-service"]="services/inventory-service"
  ["order-service"]="services/order-service"
  ["payment-service"]="services/payment-service"
  ["notification-service"]="services/notification-service"
  ["analytics-service"]="services/analytics-service"
)

for svc in "${!SERVICES[@]}"; do
  dir="${SERVICES[$svc]}"
  echo "=========================================="
  echo "Building $svc from $dir..."
  echo "=========================================="
  docker build -t "$IMAGE_PREFIX:$svc" -t "$IMAGE_PREFIX:$svc-$GIT_SHA" "/home/ubuntu/ecommerce/$dir"
  
  echo "Pushing $svc images to ECR..."
  docker push "$IMAGE_PREFIX:$svc"
  docker push "$IMAGE_PREFIX:$svc-$GIT_SHA"
done

echo "=========================================="
echo "All 8 images successfully built and pushed!"
echo "=========================================="
