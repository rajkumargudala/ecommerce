# PHP Analytics Service
FROM php:8.3-cli-alpine

WORKDIR /app

# Install PostgreSQL driver dependencies and extensions
RUN apk add --no-cache libpq-dev \
    && docker-php-ext-install pdo_pgsql

# Copy application script
COPY router.php .

# Run as non-root user
RUN addgroup -S appgroup && adduser -S appuser -G appgroup
USER appuser

EXPOSE 8087

CMD ["php", "-S", "0.0.0.0:8087", "router.php"]
