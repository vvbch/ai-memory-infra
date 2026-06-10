# Remote Streamable HTTP MCP server (ADR 034) — serves mcp.{domain} behind Caddy.
# Installs only what mcp_proxy needs (tenet 7): the full project pulls mem0ai/
# neo4j/psycopg, none of which this proxy uses. Build from the repo root:
#   docker compose -f infra/docker-compose.yml build mcp-proxy
FROM python:3.12-slim

WORKDIR /app

RUN pip install --no-cache-dir "mcp>=1.27,<2" "httpx>=0.27" "uvicorn>=0.30"

COPY src/mcp_proxy /app/mcp_proxy

ENV PYTHONPATH=/app \
    PYTHONUNBUFFERED=1

EXPOSE 8765

CMD ["python", "-m", "mcp_proxy.http_server"]
