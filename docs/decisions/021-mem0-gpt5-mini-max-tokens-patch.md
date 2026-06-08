# ADR 021: Patch mem0ai's GPT-5 detection so `gpt-5-mini` extraction works

**Status:** Accepted
**Date:** 2026-06-08
**Deciders:** Chandra

### Context

With the OpenAI project finally allowing `text-embedding-3-small` (the prior
step-4 blocker — embeddings 403 — was cleared by setting the project to "allow
all models"), the `POST /memories` round-trip stopped 502-ing but returned
`200` with an **empty** `results` list: nothing was ever stored, and `GET
/memories` + `/search` came back empty.

Root cause (from the live container logs, verified on the droplet 2026-06-08):

```
POST https://api.openai.com/v1/embeddings        -> 200 OK
POST https://api.openai.com/v1/chat/completions  -> 400 Bad Request
  "Unsupported parameter: 'max_tokens' is not supported with this model.
   Use 'max_completion_tokens' instead."
LLM extraction failed: ...
POST /memories -> 200 OK   (results: [])
```

mem0 catches the extraction failure and returns `200` with zero memories, so the
defect is **silent**: every `add` succeeds HTTP-wise but stores nothing.

The bug is in `mem0ai` **2.0.4**, `mem0/llms/base.py::_is_reasoning_model()`. Its
set of GPT-5 model names is:

```python
"gpt-5", "gpt-5o", "gpt-5o-mini", "gpt-5o-micro",
```

It lists `gpt-5o-mini` (with an "o") but **not `gpt-5-mini`** — the real OpenAI
model id we run (ADR 013). So `gpt-5-mini` falls through to the "regular model"
path (`_get_common_params`), which sends `temperature` + `max_tokens` + `top_p`.
Every real GPT-5 model rejects `max_tokens` (renamed `max_completion_tokens`) and
non-default `temperature`, so the extraction call 400s.

### Decision

**Patch `_is_reasoning_model()` to treat the whole `gpt-5*` family as reasoning
models** (so the unsupported `max_tokens`/`temperature`/`top_p` are dropped). The
patch is applied in `infra/mem0-server.Dockerfile` immediately after the
`mem0ai[graph]` install, as an idempotent `python -c` rewrite that **asserts** the
anchor still exists — so the build fails loudly if a future mem0 version
restructures the function (signalling us to drop the patch rather than silently
no-op).

We keep `gpt-5-mini` as the extraction model (ADR 013 unchanged); this is a
compatibility patch for an upstream bug, **not** a model change.

### Alternatives considered

- **Swap the extraction model to `gpt-4.1-mini`/`-nano`** (regular models that
  accept `max_tokens`): would dodge the bug with a one-line env change, but
  reverses ADR 013's deliberate `gpt-5-mini` choice (tenet 9/12) for a
  lower-quality extractor. Rejected — fix the bug, don't downgrade the model.
- **Upgrade `mem0ai` past 2.0.4:** likely fixes it upstream, but is a larger,
  less-controlled change against our from-source server build (could shift API
  behaviour). Parked — revisit when we next bump mem0 (then drop this patch; the
  build `assert` will remind us).

### Consequences (reversible — tenet 12)

- The **durable** fix lives in version control (the Dockerfile); a clean rebuild
  carries it. Reverting is a one-line `git revert`.
- **Caveat (control-plane debt):** the **currently running** container was patched
  in place (writable layer) to prove the fix and unblock step 4 **without** a
  rebuild. It survives `docker restart` and droplet reboots, but a
  `docker compose up --force-recreate` / redeploy from the *un-rebuilt* image
  would revert to the buggy library. The image must be rebuilt from this Dockerfile
  before the next redeploy — folded into the BACKLOG P1 "make the deploy
  reproducible" item.
- Validated end-to-end after the patch: `POST /memories` extracted 2 facts (event
  `ADD`); `GET /memories?user_id=diag-roundtrip-20260608` and `POST /search`
  returned them (user_id `diag-roundtrip-20260608`).

*(Sources: live droplet container logs + `mem0/llms/base.py` from the running
`mem0-api-server:local` image, mem0ai 2.0.4; verified on the droplet 2026-06-08.)*

---
