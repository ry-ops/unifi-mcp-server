# UniFi MCP Server Dockerfile
# MCP over stdio: run with `docker run -i --rm -e UNIFI_API_KEY=... ghcr.io/ry-ops/unifi-mcp-server`
FROM python:3.12-alpine

LABEL org.opencontainers.image.title="UniFi MCP Server"
LABEL org.opencontainers.image.description="MCP server for the full UniFi Network API, cloud-only through unifi.ui.com"
LABEL org.opencontainers.image.source="https://github.com/ry-ops/unifi-mcp-server"
LABEL org.opencontainers.image.vendor="ry-ops"
LABEL org.opencontainers.image.licenses="MIT"

RUN apk add --no-cache ca-certificates

WORKDIR /app

# Install uv for fast Python package management
RUN pip install --no-cache-dir uv

# Install dependencies first for better caching
COPY pyproject.toml ./
RUN uv pip install --system -r pyproject.toml

# Copy application code (.dockerignore keeps secrets.env out)
COPY main.py ./
COPY unifi_mcp/ ./unifi_mcp/
COPY specs/ ./specs/

# Create non-root user
RUN addgroup -g 1001 -S unifi && \
    adduser -S -u 1001 -G unifi unifi && \
    chown -R unifi:unifi /app

USER unifi

ENV PYTHONUNBUFFERED=1

CMD ["python", "main.py"]
