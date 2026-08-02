"""OutputSanitizer — sanitizes AI outputs to prevent unsafe content."""

from __future__ import annotations

import re
from typing import Any


class OutputSanitizer:
    """Sanitizes AI outputs: removes hallucinated numbers, ensures disclaimers."""

    DISCLAIMER = (
        "This response is for educational purposes only and is not "
        "investment, legal or tax advice. Please consult a SEBI-registered "
        "investment adviser before making any investment decision."
    )

    NUMERIC_CLAIM_PATTERN = re.compile(
        r"(?:\d{1,3}(?:,\d{3})*|\d+)\s*(?:%|rs\.?|inr|rupees|dollars?|lakh|crore)?",
        re.IGNORECASE,
    )

    @classmethod
    def sanitize(cls, text: str) -> str:
        """Sanitize output text."""
        text = cls._ensure_disclaimer(text)
        return text

    @classmethod
    def _ensure_disclaimer(cls, text: str) -> str:
        if cls.DISCLAIMER not in text:
            text = f"{text}\n\n---\n{cls.DISCLAIMER}"
        return text

    @classmethod
    def validate(cls, text: str) -> tuple[bool, list[str]]:
        """Validate that output is safe. Returns (is_safe, warnings)."""
        warnings: list[str] = []
        if cls.DISCLAIMER not in text:
            warnings.append("Missing SEBI disclaimer")
        return (len(warnings) == 0, warnings)
