# Node.js Inventory Service
FROM node:20-alpine

WORKDIR /app

# Install dependencies
COPY package*.json ./
RUN npm ci --omit=dev

# Copy source code
COPY src ./src

# Use non-root user provided by node image
USER node

EXPOSE 8083

CMD ["npm", "start"]
