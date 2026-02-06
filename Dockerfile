# UniFi MCP Server Dockerfile
FROM python:3.12-alpine

LABEL org.opencontainers.image.title="UniFi MCP Server"
LABEL org.opencontainers.image.description="MCP server for UniFi Network management"
LABEL org.opencontainers.image.source="https://github.com/ry-ops/unifi-mcp-server"
LABEL org.opencontainers.image.vendor="ry-ops"

RUN apk add --no-cache ca-certificates curl

WORKDIR /app

# Install uv for fast Python package management
RUN pip install --no-cache-dir uv

# Copy dependency files first for better caching
COPY pyproject.toml ./

# Install dependencies
RUN uv pip install --system -e .

# Copy application code
COPY . .

# Create non-root user
RUN addgroup -g 1001 -S unifi && \
    adduser -S -u 1001 -G unifi unifi && \
    chown -R unifi:unifi /app

USER unifi

ENV PYTHONUNBUFFERED=1
ENV MCP_SERVER_TYPE=unifi

EXPOSE 3000

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:3000/health || exit 1

CMD ["python", "main.py"]
