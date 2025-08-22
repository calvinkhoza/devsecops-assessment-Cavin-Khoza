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

# Set working directory
WORKDIR /build

# Copy package files first (for caching)
COPY package.json package-lock.json ./

# Install dependencies using npm ci
RUN npm ci --ignore-scripts && npm cache clean --force

# Copy source code
COPY . .

# Build the production-ready React app
RUN npm run build

# === Stage 2: Runtime Stage with Nginx ===
FROM nginx:1.25-alpine AS runtime

LABEL stage="runtime"
LABEL app.name="devsecops-react-app"
LABEL app.version="1.0.0"
LABEL security.non-root="true"

# Install runtime utilities
RUN apk update && apk upgrade && apk add --no-cache dumb-init wget && rm -rf /var/cache/apk/*

# Remove default nginx content
RUN rm -rf /usr/share/nginx/html/*

# Copy built app from build stage
COPY --from=builder /build/build /usr/share/nginx/html

# Set non-root user
RUN addgroup -g 1001 -S appgroup && adduser -S -D -H -u 1001 -G appgroup appuser
RUN chown -R appuser:appgroup /usr/share/nginx/html

USER appuser

# Expose HTTP port
EXPOSE 8080

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:8080/health || exit 1

# Start Nginx with dumb-init
ENTRYPOINT ["dumb-init", "--"]
CMD ["nginx", "-g", "daemon off;"]
