# ADR 004: ChromeOS for mobile AI workstation

**Status:** Accepted
**Date:** 2026-06-04

### Context

Need a portable device to use AI tools (Claude, ChatGPT, Gemini, DeepSeek) with full memory enrichment via the OpenMemory Chrome extension, away from the home workstation. Options: Android tablet with SIM, Chromebook, or Windows laptop.

### Decision

ASUS Chromebook CX1405 (₹30,990) — ChromeOS, Intel N50, 8GB RAM, 128GB SSD, 14" FHD.

### Why ChromeOS, not Android

Chrome on Android does NOT support extensions. The OpenMemory Chrome extension — the entire memory injection mechanism — only works on desktop Chrome (and Chromium browsers). ChromeOS runs real desktop Chrome with full native extension support. Android tablets would require Kiwi Browser as a workaround, which is a fragile third-party dependency where extension compatibility is not guaranteed.

PrimeOS (Android-based laptop OS, e.g., Primebook) was explicitly rejected for the same reason — it's Android under the hood, so Chrome extensions don't work natively.

### Why this specific model

- ASUS CX1405 over Acer CB314: Intel N50 is newer/faster than Celeron N4500, 128GB SSD vs 64GB eMMC, and ₹6,000 cheaper.
- ₹30,990 listing over ₹36,990 listing: same model (CX1405CTA-S60622), same seller (Clicktech Retail via Amazon FBA), same specs. The ₹36,990 listing appears to be a new ASIN with a fresh review pool (3.7 stars/8 reviews vs 2.7 stars/10 reviews on the older listing). Classic Amazon catalog practice.
- 8GB over 4GB: Chrome with 5+ LLM tabs + OpenMemory extension running in background consumes ~3-4GB. At 4GB total, ChromeOS overhead (~1.5GB) leaves insufficient headroom.

### Connectivity

No SIM card slot — WiFi only. Phone hotspot provides internet. SIM-equipped options were evaluated (Samsung Galaxy Tab S9 FE LTE) but rejected because they run Android (no Chrome extension support without Kiwi Browser workaround), and the SIM convenience only saves one tap (enabling hotspot). Not worth the compatibility risk.

### Consequences

- **Positive:** Full Chrome extension support, identical to desktop experience. Lightweight (1.39kg), 13.8hr battery, under ₹31K.
- **Negative:** 14" form factor is a laptop, not a tablet. Not pocketable. Can't do development work (ChromeOS Linux container too constrained on N50/8GB for Docker or Python backtesting). Claude Code Remote Control bridges this — connect to ExpertBook/Alienware at home for compute.

### Update (2026-06): Kiwi Browser is dead

Kiwi Browser — the Android workaround this ADR already flagged as fragile — was
archived and discontinued in January 2025 and pulled from the Play Store; its
extension code was merged into Microsoft Edge Canary. This *strengthens* the
decision: ChromeOS (real desktop Chrome) is the only first-class mobile path for
extension-based memory. Android extension coverage is now best-effort via a
maintained Kiwi successor (Edge Canary / Quetta), otherwise it's a known gap
alongside iOS non-Claude LLMs. The architecture and `AGENTS.md` reflect this.

---
