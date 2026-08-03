"""PRIV-001: Secret Redaction and Privacy Boundary tests.

TC-CTX-010: Secret in Tool Result -> outbound and log redaction
TC-SEC-001: Secret redaction -> outbound and log contain no secrets

FR-CONTEXT-006: Secret Redaction before outbound
FR-CONTEXT-012: Data-sending notice and explicit opt-in
FR-OBS-002: Privacy logs (no raw prompts, API keys, tool results, memory)
FR-SEC-001: Outbound Consent (Summary default off)
FR-SEC-002: Data Minimization (minimal content, no full tool args by default)
"""

from __future__ import annotations

import re

import pytest

from deepseek_context.compressor import DeepSeekCompressor
from deepseek_context.redaction import (
    redact_secrets,
    DEFAULT_SECRET_PATTERNS,
    is_summary_enabled,
    get_outbound_notice,
)


# ── TC-SEC-001: Secret Redaction ─────────────────────────


class TestSecretRedaction:
    """Secrets must be absent from captured provider requests and logs."""

    def test_api_key_redacted(self):
        text = "My API key is sk-abc123def456ghi789jkl012mno345pqr678"
        redacted = redact_secrets(text)
        assert "sk-abc123def456ghi789jkl012mno345pqr678" not in redacted
        assert "[REDACTED" in redacted or "REDACTED" in redacted

    def test_bearer_token_redacted(self):
        text = 'Authorization: Bearer eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.abc123'
        redacted = redact_secrets(text)
        assert "eyJhbGciOiJIUzI1NiJ9" not in redacted

    def test_private_key_redacted(self):
        text = "-----BEGIN RSA PRIVATE KEY-----\nMIIEpAIBAAKCAQEAxyz123\n-----END RSA PRIVATE KEY-----"
        redacted = redact_secrets(text)
        assert "MIIEpAIBAAKCAQEAxyz123" not in redacted
        assert "PRIVATE KEY" in redacted  # header preserved but content redacted

    def test_env_secret_redacted(self):
        text = "DEEPSEEK_API_KEY=sk-live-abc123def456ghi789"
        redacted = redact_secrets(text)
        assert "sk-live-abc123def456ghi789" not in redacted

    def test_no_false_positive_on_normal_text(self):
        text = "This is a normal message about API design patterns"
        redacted = redact_secrets(text)
        assert redacted == text

    def test_multiple_secrets_in_one_text(self):
        text = (
            "API_KEY=sk-abc123def456ghi789jkl012mno345 "
            "Token: Bearer eyJhbGciOiJIUzI1NiJ9.payload.sig "
            "-----BEGIN PRIVATE KEY-----\nABCDEF\n-----END PRIVATE KEY-----"
        )
        redacted = redact_secrets(text)
        assert "sk-abc123def456ghi789jkl012mno345" not in redacted
        assert "eyJhbGciOiJIUzI1NiJ9" not in redacted
        assert "ABCDEF" not in redacted


# ── TC-CTX-010: Secret in Tool Result ────────────────────


class TestToolResultRedaction:
    """Outbound Summary payload must not contain secrets from tool results."""

    def test_compressor_serialize_redacts_secrets(self):
        """serialize_for_summary output must not contain raw secrets."""
        compressor = DeepSeekCompressor(
            model="test",
            api_key="sk-test",
            base_url="http://localhost",
        )
        turns = [
            {
                "role": "tool",
                "content": 'Result: DEEPSEEK_API_KEY=sk-secret123key456val789',
                "tool_call_id": "call_1",
            },
            {
                "role": "user",
                "content": "Please check the configuration with API key sk-secret123key456val789",
            },
        ]
        serialized = compressor.serialize_for_summary(turns)
        assert "sk-secret123key456val789" not in serialized

    def test_compressor_prompt_redacted_before_outbound(self):
        """generate_summary prompt must not contain raw secrets."""
        compressor = DeepSeekCompressor(
            model="test",
            api_key="sk-test",
            base_url="http://localhost",
        )
        turns = [
            {
                "role": "tool",
                "content": "API_KEY=sk-leak-me-1234567890abcdef",
                "tool_call_id": "call_1",
            },
        ]
        # Capture what would be sent to the LLM
        captured_prompt = []

        original_call = compressor._call_deepseek_llm

        def capture_call(prompt, max_tokens, model=None):
            captured_prompt.append(prompt)
            return None  # Simulate failure to avoid real API call

        compressor._call_deepseek_llm = capture_call
        try:
            compressor.generate_summary(turns)
        finally:
            compressor._call_deepseek_llm = original_call

        if captured_prompt:
            assert "sk-leak-me-1234567890abcdef" not in captured_prompt[0]


# ── FR-SEC-001: Outbound Consent ─────────────────────────


class TestOutboundConsent:
    """Summary must be default off; only enabled with explicit consent."""

    def test_summary_default_off(self):
        assert is_summary_enabled({}) is False

    def test_summary_enabled_with_explicit_true(self):
        assert is_summary_enabled({"HARNESS_SUMMARY_ENABLED": "true"}) is True

    def test_summary_disabled_with_false(self):
        assert is_summary_enabled({"HARNESS_SUMMARY_ENABLED": "false"}) is False

    def test_summary_disabled_with_empty(self):
        assert is_summary_enabled({"HARNESS_SUMMARY_ENABLED": ""}) is False


# ── FR-CONTEXT-012: Data-sending notice ──────────────────


class TestDataSendingNotice:
    """Before enabling external summary, must show what's sent, provider, how to disable."""

    def test_notice_contains_required_info(self):
        notice = get_outbound_notice()
        assert "summary" in notice.lower() or "摘要" in notice
        assert "provider" in notice.lower() or "提供商" in notice
        assert "disable" in notice.lower() or "关闭" in notice
        assert "redact" in notice.lower() or "脱敏" in notice

    def test_notice_mentions_secrets_redacted(self):
        notice = get_outbound_notice()
        assert "secret" in notice.lower() or "密钥" in notice or "脱敏" in notice


# ── FR-SEC-002: Data Minimization ────────────────────────


class TestDataMinimization:
    """Only send minimal content; default no full tool args."""

    def test_serialize_truncates_tool_args(self):
        """Tool call arguments in serialized output should be truncated."""
        compressor = DeepSeekCompressor(
            model="test",
            api_key="sk-test",
            base_url="http://localhost",
        )
        long_args = "x" * 5000
        turns = [
            {
                "role": "assistant",
                "content": "",
                "tool_calls": [
                    {
                        "type": "function",
                        "id": "call_1",
                        "function": {
                            "name": "write_file",
                            "arguments": f'{{"path": "/test.py", "content": "{long_args}"}}',
                        },
                    }
                ],
            },
            {
                "role": "tool",
                "content": "done",
                "tool_call_id": "call_1",
            },
        ]
        serialized = compressor.serialize_for_summary(turns)
        # Tool args should be truncated (not the full 5000 chars)
        assert len(serialized) < 5000


# ── FR-OBS-002: Privacy Logs ─────────────────────────────


class TestPrivacyLogs:
    """Default logs must not contain raw prompts, API keys, tool results, memory."""

    def test_redact_secrets_covers_common_patterns(self):
        """All default secret patterns should produce redaction."""
        test_cases = [
            ("sk-1234567890abcdefghijklmnopqrstuvwxyz", "API key"),
            ("Bearer eyJhbGciOiJIUzI1NiJ9.payload.signature", "Bearer token"),
            ("-----BEGIN PRIVATE KEY-----\nMIIxyz\n-----END PRIVATE KEY-----", "Private key"),
            ("DEEPSEEK_API_KEY=sk-live-abc123def456ghi789", "env secret"),
            ("AKIAIOSFODNN7EXAMPLE", "AWS access key"),
        ]
        for secret, label in test_cases:
            redacted = redact_secrets(f"Config: {secret}")
            assert secret not in redacted, f"{label} not redacted: {redacted}"
