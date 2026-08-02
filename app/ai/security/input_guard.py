"""PromptInjectionGuard — detects and blocks prompt injection attempts."""

from __future__ import annotations

import re
from typing import Any


class PromptInjectionGuard:
    """Detects prompt injection, jailbreaking, and system prompt leakage attempts."""

    SENSITIVE_PATTERNS: list[re.Pattern] = [
        re.compile(r"ignore\s+(all\s+)?(previous|above|below)", re.IGNORECASE),
        re.compile(r"forget\s+(all\s+)?(previous|above)", re.IGNORECASE),
        re.compile(r"system\s+(prompt|instruction|message)", re.IGNORECASE),
        re.compile(r"you\s+are\s+(now|not\s+an?\s+AI)", re.IGNORECASE),
        re.compile(r"act\s+as\s+if", re.IGNORECASE),
        re.compile(r"pretend\s+(to\s+be|that)", re.IGNORECASE),
        re.compile(r"reveal\s+(your|the)\s+(prompt|instructions)", re.IGNORECASE),
        re.compile(r"output\s+(your|the)\s+(prompt|instructions)", re.IGNORECASE),
        re.compile(r"print\s+(your|the)\s+(prompt)", re.IGNORECASE),
        re.compile(r"do\s+(not\s+)?(calculate|compute|estimate)", re.IGNORECASE),
        re.compile(r"bypass", re.IGNORECASE),
        re.compile(r"jailbreak", re.IGNORECASE),
        re.compile(r"dang\w+\s+mode", re.IGNORECASE),
        re.compile(r"MAXIMUM|OVERDRIVE|GODMODE", re.IGNORECASE),
    ]

    @classmethod
    def check(cls, text: str) -> tuple[bool, list[str]]:
        """Check if text contains prompt injection attempts.

        Returns (is_safe, list_of_reasons).
        """
        issues: list[str] = []
        for pattern in cls.SENSITIVE_PATTERNS:
            if pattern.search(text):
                issues.append(f"Pattern matched: {pattern.pattern}")
        return (len(issues) == 0, issues)

    @classmethod
    def sanitize(cls, text: str) -> str:
        """Remove or neutralize injection attempts."""
        safe, issues = cls.check(text)
        if safe:
            return text
        for pattern in cls.SENSITIVE_PATTERNS:
            text = pattern.sub("[redacted]", text)
        return text
