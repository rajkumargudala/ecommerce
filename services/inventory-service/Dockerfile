# Node.js Inventory Service
FROM node:24-alpine3.24

WORKDIR /app

# Install dependencies
COPY package*.json ./
RUN npm ci --omit=dev \
    && rm -rf /usr/local/lib/node_modules/npm /usr/local/bin/npm /usr/local/bin/npx \
    && apk upgrade --no-cache

# Copy source code
COPY src ./src

# Use non-root user provided by node image
USER node

EXPOSE 8083

CMD ["node", "src/index.js"]
