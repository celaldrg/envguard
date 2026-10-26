"""Heuristics for values that look like real credentials."""

from __future__ import annotations

import math
import re
from collections import Counter

PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("AWS access key", re.compile(r"\b(AKIA|ASIA)[0-9A-Z]{16}\b")),
    ("GitHub token", re.compile(r"\b(ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9]{36,}\b|\bgithub_pat_[A-Za-z0-9_]{50,}\b")),
    ("Slack token", re.compile(r"\bxox[abprs]-[A-Za-z0-9-]{10,}\b")),
    ("Stripe live key", re.compile(r"\b(sk|rk)_live_[A-Za-z0-9]{16,}\b")),
    ("OpenAI-style key", re.compile(r"\bsk-(proj-)?[A-Za-z0-9_-]{20,}\b")),
    ("Google API key", re.compile(r"\bAIza[0-9A-Za-z_-]{35}\b")),
    ("private key", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
    ("JWT", re.compile(r"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\b")),
    ("password in URL", re.compile(r"\b[a-z][a-z0-9+.-]*://[^\s:/@]+:([^\s@/]{3,})@")),
]

PLACEHOLDER_RE = re.compile(
    r"^(|x+|\*+|\.\.\.|<.*>|\{\{.*\}\}|\$\{.*\}|change[-_ ]?me.*|your[-_ ].*|replace[-_ ]?me.*|todo|tbd|example.*|placeholder.*|secret|password|none|null|test|dummy.*|fake.*|sample.*)$",
    re.IGNORECASE,
)
URL_PLACEHOLDER_PASSWORDS = {"password", "pass", "postgres", "root", "secret", "changeme", "example", "user", "admin"}


def entropy(s: str) -> float:
    if not s:
        return 0.0
    n = len(s)
    return -sum(c / n * math.log2(c / n) for c in Counter(s).values())


def looks_secret(value: str) -> str | None:
    """Return a reason if the value looks like a real credential, else None."""
    v = value.strip()
    if PLACEHOLDER_RE.match(v):
        return None
    for name, rx in PATTERNS:
        m = rx.search(v)
        if m:
            if name == "password in URL" and m.group(1).lower() in URL_PLACEHOLDER_PASSWORDS | {"${password}"}:
                continue
            return name
    if len(v) >= 24 and " " not in v and "/" not in v.strip("/") and entropy(v) >= 4.0:
        classes = sum(bool(re.search(p, v)) for p in (r"[a-z]", r"[A-Z]", r"[0-9]"))
        if classes >= 2:
            return f"high-entropy string (entropy {entropy(v):.1f})"
    return None
