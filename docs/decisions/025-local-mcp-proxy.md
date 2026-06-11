# ADR 025: Local MCP proxy over the live REST API

Date: 2026-06-08

## Status

Accepted

## Context

Phase 4 needs Claude Code, Cursor, and VS Code to reach the same live memory store
through MCP. The deployed `memory.example.com` Mem0 API exposes REST routes
(`/memories`, `/search`) but returns `404` for the expected MCP routes (`/mcp`,
`/mcp/.../http/...`, `/mcp/.../sse/...`). OpenAPI confirms no MCP path is currently
served by our self-hosted build.

## Decision

Add a small local stdio MCP proxy in this repo. MCP clients start it locally; the
proxy calls the live REST API over HTTPS using `X-API-Key` from the local
environment.

Initial tools:

- `search_memories`
- `add_memory`
- `list_memories`

## Consequences

- No second brain: all data still lives in the live Mem0/Postgres/Neo4j stack.
- No secret in git: the local client sets `AI_MEMORY_API_KEY`; docs show only the
  variable name.
- Works for developer tools that can run stdio MCP servers: Cursor, VS Code, and
  Claude Code.
- Claude mobile/iOS remote connector still needs a later HTTP MCP endpoint because
  mobile apps cannot start a local stdio process.
