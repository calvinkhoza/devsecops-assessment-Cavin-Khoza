# Build stage
FROM node:18-alpine AS builder

WORKDIR /app

# Copy package files from src/ directory and install dependencies
COPY src/package*.json ./
RUN npm ci --omit=dev

# Copy source code from src/ directory
COPY src/ .

# Build the React app
RUN npm run build

# Runtime stage
FROM nginx:alpine AS runtime

# Install curl for healthcheck
RUN apk add --no-cache curl

# Copy built app to nginx
COPY --from=builder /app/build /usr/share/nginx/html

# Create a non-root user
RUN addgroup -g 1001 -S appgroup && \
    adduser -u 1001 -S appuser -G appgroup && \
    chown -R appuser:appgroup /var/cache/nginx && \
    chown -R appuser:appgroup /var/run && \
    chown -R appuser:appgroup /usr/share/nginx/html

USER appuser

# Expose port 80 (nginx default)
EXPOSE 80

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:80 || exit 1

# Nginx runs automatically