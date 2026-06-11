# Browser extension lives in its own repo

Phase 3's Chrome/Chromium extension is **not vendored in this infra repo**.

Decision: fork `mem0ai/mem0-chrome-extension` (MIT) into a separate **private** GitHub repo,
then rewire it to our self-hosted server (`https://memory.example.com`) using `X-API-Key`.

Why separate:

- The extension has a separate Node/TypeScript/Vite toolchain and Chrome Web Store release
  lifecycle.
- A real fork should preserve upstream history and attribution cleanly.
- Keeping it private while we rewrite avoids public confusion while the raw fork still looks
  like upstream.

See `docs/decisions/024-chrome-extension-fork.md` and `docs/planning/STATUS.md` for the
current plan and resume point.
