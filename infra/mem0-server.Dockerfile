# Build the Mem0 REST API server for linux/amd64 from source.
#
# Why this exists: the published `mem0/mem0-api-server:latest` image is
# arm64-only (no linux/amd64 manifest), so it cannot run on the amd64 droplet.
# We build from the mem0ai/mem0 `server/` directory instead. We also install the
# graph-store extras (`mem0ai[graph]`, `langchain-neo4j`, `rank-bm25`) following
# the Mem0 self-host guide. NOTE (ADR 032): as of mem0ai 2.0.4 the `server/` app
# never reads `NEO4J_*` and ships no graph-store code, so these extras are
# currently INERT (`mem0ai[graph]` resolves to plain mem0ai with a warning). They
# are kept as forward-leaning scaffolding for a future graph-capable Mem0; Neo4j
# is written only by LifeGraph (Phase 6, not yet built), not by Mem0 today.
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

# Patch mem0ai's GPT-5 detection (bug as of mem0ai 2.0.4): _is_reasoning_model()
# lists "gpt-5o-mini" but NOT "gpt-5-mini", so our configured `gpt-5-mini` is
# treated as a regular model and sent `max_tokens`, which every real GPT-5 model
# rejects (400 unsupported_parameter) -> LLM fact-extraction silently fails and
# every `add` returns 0 memories. We mark the whole gpt-5* family as reasoning so
# the unsupported params (max_tokens/temperature) are dropped. The `assert` fails
# the build loudly if a future mem0 version restructures this code (so we notice
# and drop the patch instead of silently no-op'ing). See STATUS.md / ADR.
RUN python -c "import mem0.llms.base as b, pathlib; p=pathlib.Path(b.__file__); s=p.read_text(); marker='# mem0-gpt5-patch'; anchor='if base_model in reasoning_models:\n            return True\n'; q=chr(39); ins=anchor+'\n        '+marker+'\n        if base_model.startswith('+q+'gpt-5'+q+'):\n            return True\n'; assert marker in s or anchor in s, 'mem0 base.py gpt-5 patch anchor not found - review _is_reasoning_model'; p.write_text(s if marker in s else s.replace(anchor, ins, 1))"

COPY . .

EXPOSE 8000
ENV PYTHONUNBUFFERED=1

# Production: no --reload (the upstream dev CMD watches files; we don't want that).
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
