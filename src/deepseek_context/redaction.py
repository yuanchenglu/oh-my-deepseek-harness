"""PRIV-001: Secret Redaction and Privacy Boundary enforcement.

FR-CONTEXT-006: Redact API Key, Bearer Token, Private Key, .env Secret, cloud credentials before outbound.
FR-CONTEXT-012: Data-sending notice with provider, content, disable method, redaction scope.
FR-OBS-002: Default logs must not contain raw prompts, API keys, tool results, memory.
FR-SEC-001: Summary default off; only enable with explicit consent.
FR-SEC-002: Data Minimization — only send minimal content, default no full tool args.
"""

from __future__ import annotations

import os
import re
from typing import Any, Mapping


# ── Secret patterns ──────────────────────────────────────

# OpenAI-style API keys: sk- followed by 20+ alphanumeric chars
_API_KEY_RE = re.compile(r"sk-[a-zA-Z0-9]{20,}")

# Bearer tokens: Bearer <jwt or long token>
_BEARER_RE = re.compile(r"(Bearer\s+)([a-zA-Z0-9_\-.]{20,})", re.IGNORECASE)

# PEM private key blocks
_PRIVATE_KEY_RE = re.compile(
    r"(-----BEGIN\s+(?:RSA\s+|EC\s+|OPENSSH\s+|)PRIVATE KEY-----)"
    r"[\s\S]*?"
    r"(-----END\s+(?:RSA\s+|EC\s+|OPENSSH\s+|)PRIVATE KEY-----)",
    re.MULTILINE,
)

# .env style: KEY=sk-... or KEY=<long hex/base64 secret>
_ENV_SECRET_RE = re.compile(
    r"((?:API_KEY|SECRET|TOKEN|PASSWORD|CREDENTIAL|PRIVATE_KEY|ACCESS_KEY)"
    r"(?:\s*=\s*))"
    r"([a-zA-Z0-9_\-/.+]{16,})",
    re.IGNORECASE,
)

# AWS Access Key ID
_AWS_KEY_RE = re.compile(r"\bAKIA[0-9A-Z]{16}\b")

# AWS Secret Access Key (40 char base64)
_AWS_SECRET_RE = re.compile(r"\b([a-zA-Z0-9/+=]{40})\b")

# Generic high-entropy hex/base64 secrets (32+ chars, no spaces)
# Only match when preceded by key-like context to avoid false positives
_GENERIC_SECRET_RE = re.compile(
    r"(?:secret|token|key|password|credential|auth)"
    r"['\"]?\s*[:=]\s*['\"]?"
    r"([a-zA-Z0-9_\-/+=]{32,})",
    re.IGNORECASE,
)

DEFAULT_SECRET_PATTERNS = (
    _API_KEY_RE,
    _BEARER_RE,
    _PRIVATE_KEY_RE,
    _ENV_SECRET_RE,
    _AWS_KEY_RE,
)


def redact_secrets(text: str) -> str:
    """Redact known secret patterns from text.

    Replaces secrets with [REDACTED:TYPE] markers.
    Preserves surrounding structure (JSON keys, env var names, headers).
    """
    if not text:
        return text

    # API keys
    text = _API_KEY_RE.sub("[REDACTED:API_KEY]", text)

    # Bearer tokens (preserve "Bearer " prefix)
    text = _BEARER_RE.sub(r"\1[REDACTED:BEARER]", text)

    # PEM private keys (replace entire block including content)
    def _redact_pem(m: re.Match) -> str:
        header = m.group(1)
        return f"{header}\n[REDACTED:PRIVATE_KEY_CONTENT]\n-----END PRIVATE KEY-----"
    text = _PRIVATE_KEY_RE.sub(_redact_pem, text)

    # .env style secrets (preserve KEY= prefix)
    text = _ENV_SECRET_RE.sub(r"\1[REDACTED:ENV_SECRET]", text)

    # AWS Access Key IDs
    text = _AWS_KEY_RE.sub("[REDACTED:AWS_KEY]", text)

    # Generic key=value secrets
    def _redact_generic(m: re.Match) -> str:
        full = m.group(0)
        secret = m.group(1)
        return full[:len(full) - len(secret)] + "[REDACTED:SECRET]"
    text = _GENERIC_SECRET_RE.sub(_redact_generic, text)

    return text


# ── FR-SEC-001: Outbound Consent ─────────────────────────

_SUMMARY_ENABLED_ENV = "HARNESS_SUMMARY_ENABLED"


def is_summary_enabled(env: Mapping[str, str] | None = None) -> bool:
    """Summary is default OFF. Only explicit 'true'/'1'/'yes' enables it."""
    env_map = os.environ if env is None else env
    val = env_map.get(_SUMMARY_ENABLED_ENV, "").strip().lower()
    return val in {"true", "1", "yes", "on"}


# ── FR-CONTEXT-012: Data-sending notice ──────────────────

_OUTBOUND_NOTICE = (
    "[PRIVACY NOTICE] External Summary is about to be enabled.\n"
    "What will be sent: A compressed summary of earlier conversation turns.\n"
    "Provider: The configured DeepSeek-compatible LLM provider.\n"
    "Redaction: API keys, Bearer tokens, private keys, .env secrets and cloud "
    "credentials are redacted before sending. Tool arguments are truncated.\n"
    "To disable: Set HARNESS_SUMMARY_ENABLED=false or leave unset (default off).\n"
    "To minimize: Set HARNESS_SUMMARY_ALLOW_TOOL_ARGUMENTS=false (default) to "
    "strip full tool arguments from the outbound payload."
)


def get_outbound_notice() -> str:
    """Return the mandatory data-sending notice shown before enabling Summary."""
    return _OUTBOUND_NOTICE


# ── Integration hook for compressor ──────────────────────


def redact_outbound_payload(text: str) -> str:
    """Apply all redaction layers to text before sending to external provider.

    Called by compressor.serialize_for_summary() and generate_summary()
    before any data leaves the local process.
    """
    return redact_secrets(text)
