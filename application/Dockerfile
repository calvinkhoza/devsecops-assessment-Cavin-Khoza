# ==========================================
# Multi-stage Dockerfile for React Application
# Fully Secure, DevSecOps-ready
# Works without package.json
# ==========================================

# Stage 1: Build React App
# ==========================================
FROM node:18-alpine AS builder

LABEL maintainer="devsecops@company.com"
LABEL stage="builder"
LABEL security.scan="enabled"
LABEL version="1.0.0"

# Install essential tools
RUN apk update && apk upgrade && apk add --no-cache \
    dumb-init \
    ca-certificates \
    && rm -rf /var/cache/apk/*

# Create non-root user
RUN addgroup -g 1001 -S appgroup && \
    adduser -S -D -H -u 1001 -s /sbin/nologin -G appgroup appuser

WORKDIR /app
RUN chown appuser:appgroup /app

USER appuser

# Copy package-lock.json only
COPY --chown=appuser:appgroup application/package-lock.json ./

# Create dummy package.json so npm can install from lockfile
RUN echo '{"name":"react-app","version":"1.0.0","private":true,"dependencies":{}}' > package.json

# Install dependencies strictly from lockfile
RUN npm ci --ignore-scripts --no-audit --no-fund && npm cache clean --force

# Copy the rest of the app
COPY --chown=appuser:appgroup application/ ./

# Build React app
RUN npm run build && rm -rf node_modules && npm cache clean --force

# ==========================================
# Stage 2: Production Runtime with Nginx
# ==========================================
FROM nginx:1.25-alpine AS runtime

LABEL maintainer="devsecops@company.com"
LABEL stage="runtime"
LABEL security.scan="enabled"
LABEL version="1.0.0"

# Install essential tools
RUN apk update && apk upgrade && apk add --no-cache \
    dumb-init \
    ca-certificates \
    wget \
    && rm -rf /var/cache/apk/*

# Create non-root user
RUN addgroup -g 1001 -S appgroup && \
    adduser -S -D -H -u 1001 -s /sbin/nologin -G appgroup appuser

# Remove default nginx content
RUN rm -rf /usr/share/nginx/html/* && rm -rf /etc/nginx/conf.d/default.conf

# Copy built React app
COPY --from=builder --chown=appuser:appgroup /app/build /usr/share/nginx/html

# Nginx config with security headers and SPA routing
RUN cat > /etc/nginx/conf.d/default.conf << 'EOF'
server {
    listen 8080;
    server_name localhost;
    root /usr/share/nginx/html;
    index index.html;

    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self' data:;" always;
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Permitted-Cross-Domain-Policies "none" always;

    server_tokens off;

    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_comp_level 6;
    gzip_types text/plain text/css text/xml text/javascript application/javascript application/xml+rss application/json application/xml image/svg+xml;

    location / {
        try_files $uri $uri/ /index.html;
        add_header Cache-Control "no-cache, no-store, must-revalidate";
        add_header Pragma "no-cache";
        add_header Expires "0";
    }

    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot|webp|map)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
        access_log off;
    }

    location = /service-worker.js {
        expires off;
        add_header Cache-Control "no-cache, no-store, must-revalidate";
    }

    location = /health {
        access_log off;
        return 200 "healthy\n";
        add_header Content-Type text/plain;
    }

    location ~ /\.(htaccess|htpasswd|env|git) { deny all; return 404; }
    location ~* \.(log|conf|config|bak|backup)$ { deny all; return 404; }

    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    limit_req zone=api burst=20 nodelay;

    if ($http_user_agent = "") { return 444; }
    if ($request_uri ~* "(\<|%3C).*script.*(\>|%3E)") { return 403; }
}
EOF

# Configure nginx to run as non-root
RUN sed -i 's/user  nginx;/user  appuser;/' /etc/nginx/nginx.conf && \
    sed -i 's|pid /var/run/nginx.pid;|pid /tmp/nginx/nginx.pid;|' /etc/nginx/nginx.conf && \
    sed -i '/worker_processes/a worker_rlimit_nofile 1024;' /etc/nginx/nginx.conf && \
    chown -R appuser:appgroup /etc/nginx/conf.d/

USER appuser

ENV NODE_ENV=production \
    NGINX_ENTRYPOINT_QUIET_LOGS=1

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider --timeout=5 http://localhost:8080/health || exit 1

ENTRYPOINT ["dumb-init", "--"]
CMD ["nginx", "-g", "daemon off;"]
