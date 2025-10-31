# Multi-stage Dockerfile for UniFi MCP Server
# Optimized for production deployment with minimal image size

# Stage 1: Builder
FROM python:3.12-slim as builder

# Install uv for fast dependency resolution
RUN pip install --no-cache-dir uv

# Set working directory
WORKDIR /app

# Copy dependency files
COPY pyproject.toml ./
COPY uv.lock ./

# Install dependencies in a virtual environment
RUN uv venv /app/.venv && \
    . /app/.venv/bin/activate && \
    uv pip install --no-cache -e .

# Stage 2: Runtime
FROM python:3.12-slim

# Create non-root user for security
RUN groupadd -r unifi && useradd -r -g unifi unifi

# Set working directory
WORKDIR /app

# Copy virtual environment from builder
COPY --from=builder /app/.venv /app/.venv

# Copy application code
COPY main.py ./
COPY pyproject.toml ./

# Create directories for logs and config
RUN mkdir -p /app/logs /app/config && \
    chown -R unifi:unifi /app

# Switch to non-root user
USER unifi

# Set environment variables
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    UNIFI_LOG_FILE="/app/logs/unifi_mcp_audit.log" \
    UNIFI_LOG_TO_FILE="true"

# Health check (requires UNIFI_GATEWAY_HOST to be set at runtime)
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import main; result = main._health_check(); exit(0 if result.get('ok') else 1)" || exit 1

# Default command
CMD ["python", "main.py"]

# Labels
LABEL maintainer="UniFi MCP Server" \
      description="Model Context Protocol server for UniFi network equipment" \
      version="0.4.0"
