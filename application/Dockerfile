# -----------------------------
# Multi-stage Dockerfile: React + Nginx + Security
# -----------------------------

# === Stage 1: React Build Stage ===
FROM node:18-alpine AS builder

LABEL maintainer="devsecops@company.com"
LABEL version="1.0.0"
LABEL stage="builder"

# Update & add basic utilities
RUN apk update && apk upgrade && apk add --no-cache dumb-init && rm -rf /var/cache/apk/*

# Create non-root user and group
RUN addgroup -g 1001 -S appgroup && adduser -S -D -H -u 1001 -G appgroup appuser

# Set working directory
WORKDIR /build

# Copy package files first (for caching)
COPY package.json package-lock.json ./

# Install dependencies securely (using npm install instead of npm ci)
RUN npm install --legacy-peer-deps && npm cache clean --force

# Copy source code and set ownership
COPY . .

# Build the production-ready React app
RUN npm run build

# === Stage 2: Runtime Stage with Nginx ===
FROM nginx:1.25-alpine AS runtime

LABEL stage="runtime"
LABEL app.name="react-secure-app"
LABEL app.version="1.0.0"
LABEL app.description="Secure React application"
LABEL security.non-root="true"
LABEL security.readonly-rootfs="false"
LABEL security.capabilities="none"
LABEL security.user="1001:1001"
LABEL security.base-image="nginx:1.25-alpine"
LABEL security.ports="8080"
LABEL security.healthcheck="enabled"

# Install runtime dependencies
RUN apk update && apk upgrade && apk add --no-cache dumb-init wget && rm -rf /var/cache/apk/*

# Remove default nginx config
RUN rm -f /etc/nginx/conf.d/default.conf && rm -rf /usr/share/nginx/html/*

# Create necessary directories and set permissions
RUN mkdir -p /var/cache/nginx /var/run/nginx /var/log/nginx /usr/share/nginx/html && \
    addgroup -g 1001 -S appgroup && adduser -S -D -H -u 1001 -G appgroup appuser && \
    chown -R appuser:appgroup /var/cache/nginx /var/run/nginx /var/log/nginx /usr/share/nginx/html && \
    chmod -R 755 /var/cache/nginx /var/run/nginx /var/log/nginx

# Copy built app from build stage
COPY --from=builder /build/build /usr/share/nginx/html

# Set NGINX to run as non-root user
RUN sed -i 's/user  nginx;/user  appuser;/' /etc/nginx/nginx.conf && \
    sed -i '/worker_processes/a worker_rlimit_nofile 65535;' /etc/nginx/nginx.conf && \
    sed -i '/events {/a \ \ \ \ use epoll;\n\ \ \ \ worker_connections 1024;\n\ \ \ \ multi_accept on;' /etc/nginx/nginx.conf

# Set PID file for non-root use
RUN mkdir -p /tmp/nginx && \
    chown -R appuser:appgroup /tmp/nginx && \
    sed -i 's|pid /var/run/nginx.pid;|pid /tmp/nginx/nginx.pid;|' /etc/nginx/nginx.conf

# NGINX default config
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
    add_header X-Permitted-Cross-Domain-Policies "none" always;
    add_header X-Robots-Tag "none" always;

    server_tokens off;

    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_proxied expired no-cache no-store private must-revalidate max-age=0;
    gzip_types text/plain text/css text/xml text/javascript application/javascript application/xml+rss application/json application/xml image/svg+xml;

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

    location = /service-worker.js {
        expires off;
        add_header Cache-Control "no-cache, no-store, must-revalidate";
        add_header Pragma "no-cache";
        add_header Expires "0";
    }

    location = /manifest.json {
        expires 1d;
        add_header Cache-Control "public";
    }

    location ~ /\.(htaccess|htpasswd|env|git) {
        deny all;
        access_log off;
        log_not_found off;
        return 404;
    }

    location ~* \.(log|conf|config)$ {
        deny all;
        access_log off;
        log_not_found off;
        return 404;
    }

    location = /health {
        access_log off;
        return 200 "healthy\n";
        add_header Content-Type text/plain;
    }

    limit_req_zone \$binary_remote_addr zone=api:10m rate=10r/s;
    limit_req zone=api burst=20 nodelay;

    if (\$http_user_agent = "") {
        return 444;
    }

    if (\$request_uri ~* "(\<|%3C).*script.*(\>|%3E)") {
        return 403;
    }
}
EOF

# Set file ownership and permissions
RUN chown -R appuser:appgroup /etc/nginx/conf.d && chmod 644 /etc/nginx/conf.d/default.conf

# Switch to secure user
USER appuser

# Set environment variables
ENV NODE_ENV=production \
    NGINX_ENTRYPOINT_QUIET_LOGS=1

# Expose non-root HTTP port
EXPOSE 8080

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:8080/health || exit 1

# Entry point
ENTRYPOINT ["dumb-init", "--"]
CMD ["nginx", "-g", "daemon off;"]
