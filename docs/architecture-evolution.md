# Architecture evolution


The architecture went through three major pivots during the design session:

**v1 — LobeChat as unified PWA interface**
Proposed building a self-hosted LobeChat (Next.js PWA) as the chat interface for all LLMs, with Mem0 integrated at the application layer. Rejected because: (a) it duplicates inferior versions of native LLM UIs (Claude has artifacts, ChatGPT has voice mode, DeepSeek has free reasoning), (b) it adds API costs for every conversation ($5-15/M tokens), (c) the native interfaces are built by companies spending billions on UX — can't compete with a fork.

**v2 — Native UIs + market graph in same repo**
Settled on native LLM web UIs + Chrome extension for memory injection. Included the market world model graph (trading instruments, strategies, backtest results) in the same public repo. Rejected because: firm IP (strategies, backtest results, SEBI compliance) would leak into the public portfolio. When additional collaborators join and entities formalize, code ownership gets messy if firm assets live inside the public platform repo.

**v3 (final) — Two-repo pattern with LifeGraph**
Public repo is the platform + LifeGraph POC. Private domain repos plug in via REST API. LifeGraph demonstrates the same temporal graph capability without leaking IP. The "self-referential" angle ("the system models itself") is a stronger interview story than a domain-specific graph.

---
