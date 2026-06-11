"""Security and correctness guardrails (Phase 7 / ADR 007)."""

from __future__ import annotations

import re

# India PII + common secret shapes — block before write.
_AADHAAR_RE = re.compile(r"\b\d{4}\s?\d{4}\s?\d{4}\b")
_PAN_RE = re.compile(r"\b[A-Z]{5}\d{4}[A-Z]\b", re.IGNORECASE)
_OPENAI_KEY_PREFIX = "sk" + "-"
_API_KEY_RE = re.compile(
    rf"\b({_OPENAI_KEY_PREFIX}[A-Za-z0-9]{{16,}}|AIza[0-9A-Za-z_-]{{20,}})\b"
)
_INJECTION_RE = re.compile(r"(?i)(ignore previous instructions|system:\s*you are)")


def contains_pii_or_secret(text: str) -> bool:
    """Return True when text likely contains blocked PII or secrets."""
    return bool(
        _AADHAAR_RE.search(text)
        or _PAN_RE.search(text)
        or _API_KEY_RE.search(text)
    )


def contains_injection_pattern(text: str) -> bool:
    """Return True for obvious prompt-injection phrases."""
    return bool(_INJECTION_RE.search(text))


def should_reject_memory_write(text: str) -> tuple[bool, str | None]:
    """Gate memory writes — (reject?, reason)."""
    if contains_pii_or_secret(text):
        return True, "pii_or_secret"
    if contains_injection_pattern(text):
        return True, "injection_pattern"
    return False, None
