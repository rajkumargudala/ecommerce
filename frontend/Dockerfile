# Build stage
FROM node:24-alpine3.24 AS builder

WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build

# Runtime stage
FROM nginx:alpine3.24

RUN apk upgrade --no-cache

COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

USER 101

EXPOSE 8080

CMD ["nginx", "-g", "daemon off;"]
