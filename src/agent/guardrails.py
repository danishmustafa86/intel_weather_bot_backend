"""Input and output guardrails for the agent.

Rule-based checks (fast, free, no extra LLM call):
- Input: empty / too long messages, prompt-injection attempts, clearly harmful requests.
- Output: redact anything that looks like a secret / API key, and cap the length.
"""

import re
from dataclasses import dataclass

MAX_INPUT_CHARS = 4000
MAX_OUTPUT_CHARS = 12000


@dataclass
class GuardrailResult:
    allowed: bool
    reason: str = ""
    message: str = ""  # text that is safe to use (possibly modified)


PROMPT_INJECTION_PATTERNS = [
    r"ignore\s+(all\s+)?(the\s+)?(previous|prior|above)\s+(instructions|prompts?|rules)",
    r"disregard\s+(all\s+)?(the\s+)?(previous|prior|above|your)\s+(instructions|rules)",
    r"(reveal|show|print|repeat|leak)\s+(me\s+)?(your|the)\s+(system\s+prompt|instructions|hidden\s+prompt)",
    r"(reveal|show|print|give)\s+(me\s+)?(your|the)\s+(api[\s_-]?keys?|secrets?|env(ironment)?\s+variables?|\.env)",
    r"you\s+are\s+now\s+(in\s+)?(dan|developer\s+mode|jailbroken)",
    r"\bjailbreak\b",
]

HARMFUL_PATTERNS = [
    r"\b(make|build|create|synthesi[sz]e)\b.{0,40}\b(bomb|explosive|nerve\s+agent|bioweapon|chemical\s+weapon)\b",
    r"\b(child\s+(porn|sexual\s+abuse))\b",
    r"\bhow\s+to\s+(kill|murder|poison)\s+(someone|a\s+person|people|my)\b",
    r"\b(write|create|make)\b.{0,30}\b(ransomware|keylogger|malware)\b",
]

SECRET_PATTERNS = [
    r"AIza[0-9A-Za-z_\-]{35}",          # Google API key
    r"gsk_[0-9A-Za-z]{20,}",            # Groq key
    r"xai-[0-9A-Za-z]{20,}",            # xAI key
    r"tvly-[0-9A-Za-z\-]{20,}",         # Tavily key
    r"sk-[0-9A-Za-z]{20,}",             # Generic OpenAI-style key
    r"mongodb(\+srv)?://[^\s:]+:[^\s@]+@[^\s]+",  # Mongo URI with password
]

_injection_re = [re.compile(p, re.IGNORECASE) for p in PROMPT_INJECTION_PATTERNS]
_harmful_re = [re.compile(p, re.IGNORECASE) for p in HARMFUL_PATTERNS]
_secret_re = [re.compile(p) for p in SECRET_PATTERNS]


def check_input(text: str) -> GuardrailResult:
    cleaned = (text or "").strip()

    if not cleaned:
        return GuardrailResult(False, "empty", "Please type a question.")

    if len(cleaned) > MAX_INPUT_CHARS:
        return GuardrailResult(
            False,
            "too_long",
            f"Your message is too long ({len(cleaned)} characters). "
            f"Please keep it under {MAX_INPUT_CHARS} characters.",
        )

    if any(p.search(cleaned) for p in _injection_re):
        return GuardrailResult(
            False,
            "prompt_injection",
            "I can't follow requests to change my instructions or reveal internal "
            "configuration. Ask me about the weather or anything you'd like me to search for!",
        )

    if any(p.search(cleaned) for p in _harmful_re):
        return GuardrailResult(
            False,
            "harmful",
            "Sorry, I can't help with that request.",
        )

    return GuardrailResult(True, message=cleaned)


def check_output(text: str) -> GuardrailResult:
    safe = text or ""
    redacted = False
    for p in _secret_re:
        safe, n = p.subn("[REDACTED]", safe)
        redacted = redacted or n > 0

    if len(safe) > MAX_OUTPUT_CHARS:
        safe = safe[:MAX_OUTPUT_CHARS] + "\n\n…(response truncated)"

    if not safe.strip():
        safe = "Sorry, I couldn't generate a response. Please try again."

    return GuardrailResult(True, "redacted" if redacted else "", safe)
