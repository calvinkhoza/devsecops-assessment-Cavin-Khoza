# -----------------------------
# Multi-stage Dockerfile: React + Nginx + Security
# -----------------------------

# === Stage 1: React Build Stage ===
FROM node:18-alpine AS builder

LABEL maintainer="devsecops@company.com"
LABEL version="1.0.0"
LABEL stage="builder"

# Add basic utilities
RUN apk update && apk upgrade && apk add --no-cache dumb-init && rm -rf /var/cache/apk/*

# Create non-root user and group
RUN addgroup -g 1001 -S appgroup && adduser -S -D -H -u 1001 -G appgroup appuser

# Set working directory
WORKDIR /build

# Copy package files first (for caching)
COPY package.json package-lock.json ./

# Install dependencies securely using npm install
RUN npm install --production && npm cache clean --force

# Copy source code
COPY . .

# Build production-ready React app
RUN npm run build

# Change ownership of build files
RUN chown -R appuser:appgroup /build

# === Stage 2: Runtime Stage with Nginx ===
FROM nginx:1.25-alpine AS runtime

LABEL stage="runtime"
LABEL app.name="react-secure-app"
LABEL app.version="1.0.0"
LABEL security.non-root="true"
LABEL security.user="1001:1001"

# Install dumb-init for proper signal handling
RUN apk update && apk upgrade && apk add --no-cache dumb-init && rm -rf /var/cache/apk/*

# Remove default nginx config and html
RUN rm -rf /usr/share/nginx/html/* /etc/nginx/conf.d/default.conf

# Create non-root user & directories
RUN addgroup -g 1001 -S appgroup && adduser -S -D -H -u 1001 -G appgroup appuser
RUN mkdir -p /usr/share/nginx/html /var/cache/nginx /var/log/nginx /var/run/nginx \
    && chown -R appuser:appgroup /usr/share/nginx/html /var/cache/nginx /var/log/nginx /var/run/nginx \
    && chmod -R 755 /usr/share/nginx/html /var/cache/nginx /var/log/nginx /var/run/nginx

# Copy React build from builder stage
COPY --from=builder /build/build /usr/share/nginx/html

# Set Nginx to run as non-root
RUN sed -i 's/user  nginx;/user  appuser;/' /etc/nginx/nginx.conf

# Nginx configuration
COPY --chown=appuser:appgroup <<EOF /etc/nginx/conf.d/default.conf
server {
    listen 8080;
    server_name localhost;
    root /usr/share/nginx/html;
    index index.html;

    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    add_header Content-Security-Policy "default-src 'self' http: https: ws: wss: data: blob: 'unsafe-inline' 'unsafe-eval'" always;

    server_tokens off;

    location / {
        try_files \$uri \$uri/ /index.html;
        add_header Cache-Control "no-cache, no-store, must-revalidate";
        add_header Pragma "no-cache";
        add_header Expires "0";
    }

    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot|webp|avif|map)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
        access_log off;
        add_header Access-Control-Allow-Origin "*";
    }

    location = /health {
        access_log off;
        return 200 "healthy\n";
        add_header Content-Type text/plain;
    }
}
EOF

# Switch to non-root user
USER appuser

# Environment variables
ENV NODE_ENV=production \
    NGINX_ENTRYPOINT_QUIET_LOGS=1

# Expose port
EXPOSE 8080

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:8080/health || exit 1

# Entrypoint
ENTRYPOINT ["dumb-init", "--"]
CMD ["nginx", "-g", "daemon off;"]
