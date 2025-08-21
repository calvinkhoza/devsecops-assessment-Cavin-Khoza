# Stage 1: Builder
FROM python:3.11-slim as builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc libc6-dev && \
    rm -rf /var/lib/apt/lists/*

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Stage 2: Final Runtime Image
FROM python:3.11-slim as runtime

# Install curl for the healthcheck and remove the apt cache in a single layer to keep image small
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl && \
    rm -rf /var/lib/apt/lists/*

# Create a non-root user and group
RUN groupadd -r appgroup && useradd -r -g appgroup appuser

# Copy the virtual environment from the builder stage
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Set the working directory and ensure it's owned by appuser
WORKDIR /app
RUN chown appuser:appgroup /app
COPY --chown=appuser:appgroup app.py .
COPY --chown=appuser:appgroup src/ ./src/

# Switch to the non-root user
USER appuser

# Expose the port the app runs on
EXPOSE 8080

# Health check (now curl is available)
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8080/health || exit 1

# Command to run the application
CMD ["python", "app.py"]