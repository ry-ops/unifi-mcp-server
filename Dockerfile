# UniFi MCP Server Dockerfile
FROM node:20-alpine

LABEL org.opencontainers.image.title="UniFi MCP Server"
LABEL org.opencontainers.image.description="MCP server for UniFi Network management"
LABEL org.opencontainers.image.source="https://github.com/ry-ops/unifi-mcp-server"
LABEL org.opencontainers.image.vendor="ry-ops"

RUN apk add --no-cache ca-certificates curl

WORKDIR /app

COPY package*.json ./

RUN npm ci --only=production && npm cache clean --force

COPY . .

RUN addgroup -g 1001 -S unifi && \
    adduser -S -u 1001 -G unifi unifi && \
    chown -R unifi:unifi /app

USER unifi

ENV NODE_ENV=production
ENV MCP_SERVER_TYPE=unifi

EXPOSE 3000

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD node -e "require('http').get('http://localhost:3000/health', (r) => process.exit(r.statusCode === 200 ? 0 : 1))" || exit 1

CMD ["node", "index.js"]
