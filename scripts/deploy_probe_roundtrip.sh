#!/usr/bin/env bash
# Throwaway add -> update -> delete against local Mem0 on the droplet (ADR 037 verify).
set -eu
cd /opt/ai-memory-infra/infra
ADMIN_API_KEY="$(grep '^ADMIN_API_KEY=' .env | cut -d= -f2-)"
BASE="http://127.0.0.1:8888"
HDR="X-API-Key: ${ADMIN_API_KEY}"
EXT="deploy-probe-037-$(date +%s)"
ADD="$(curl -fsS -X POST "${BASE}/memories" -H "${HDR}" -H "Content-Type: application/json" \
  -d "{\"messages\":[{\"role\":\"user\",\"content\":\"mcp redeploy probe ${EXT}\"}],\"user_id\":\"chandrav\",\"infer\":false,\"metadata\":{\"source\":\"deploy-probe\",\"type\":\"fact\",\"external_id\":\"${EXT}\"}}")"
MID="$(python3 - <<'PY' "${ADD}"
import json, sys
d = json.loads(sys.argv[1])
r = d.get("results") or [d]
print(r[0].get("id", ""))
PY
)"
test -n "${MID}"
curl -fsS -X PUT "${BASE}/memories/${MID}" -H "${HDR}" -H "Content-Type: application/json" \
  -d '{"text":"mcp redeploy probe updated"}' >/dev/null
curl -fsS -X DELETE "${BASE}/memories/${MID}" -H "${HDR}" >/dev/null
echo "PROBE_OK id=${MID}"
