# Build the Mem0 REST API server for linux/amd64 from source.
#
# Why this exists: the published `mem0/mem0-api-server:latest` image is
# arm64-only (no linux/amd64 manifest), so it cannot run on the amd64 droplet.
# We build from the mem0ai/mem0 `server/` directory instead. We also add the
# Neo4j graph-store extras the stock requirements.txt omits (`mem0ai[graph]`,
# `langchain-neo4j`, `rank-bm25`) — required because our stack uses Neo4j for
# the Mem0 auto-graph + LifeGraph. (Matches the Mem0 self-host guide's patch.)
#
# Build context = the mem0 source `server/` dir:
#   docker build -f mem0-server.Dockerfile -t mem0-api-server:local /opt/mem0-src/server
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
# psycopg[binary] bundles libpq + the C speedups (the stock requirements pin
# plain `psycopg`, which needs a system libpq that python:3.12-slim lacks).
RUN pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir "psycopg[binary,pool]" "mem0ai[graph]" rank-bm25 langchain-neo4j neo4j

COPY . .

EXPOSE 8000
ENV PYTHONUNBUFFERED=1

# Production: no --reload (the upstream dev CMD watches files; we don't want that).
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
