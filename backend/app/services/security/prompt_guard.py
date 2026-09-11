"""Security Prompt Injection Guard and Untrusted Document Content Sanitizer.

Treats all user inputs, uploaded PDF text, OCR transcriptions, and metadata as UNTRUSTED DATA.

Core Protection Rules:
1. Document text must NEVER become system instructions or override regulatory rules.
2. Direct system prompt injection indicators (e.g. "ignore previous instructions", "declare compliant",
   "system override", "bypass test") are flagged, neutralized, and logged as security events.
3. Untrusted document assertions (e.g. "ChatGPT said this is compliant", "BIS officer verbally approved")
   cannot satisfy evidence requirements or mutate compliance status.
"""
import re
from typing import Tuple, List
from pydantic import BaseModel, Field


class PromptGuardScanResult(BaseModel):
    is_safe: bool
    detected_patterns: List[str] = Field(default_factory=list)
    sanitized_text: str
    security_verdict: str  # CLEAN | POTENTIAL_INJECTION_FLAGGED | ADVERSARIAL_INSTRUCTION_NEUTRALIZED


# High-confidence adversarial injection patterns in user documents or OCR
INJECTION_PATTERNS = [
    (r"(?i)\bignore\s+(?:all\s+)?(?:previous|prior)\s+instructions\b", "SYSTEM_INSTRUCTION_OVERRIDE"),
    (r"(?i)\bdeclare\s+(?:this\s+product\s+)?(?:fully\s+)?compliant\b", "FORCED_COMPLIANCE_ASSERTION"),
    (r"(?i)\bbypass\s+(?:all\s+)?(?:testing|checks?|validation|leakage|rules?)\b", "TEST_BYPASS_ATTEMPT"),
    (r"(?i)\byou\s+are\s+now\s+(?:in\s+)?(?:dan|developer|admin|god)\s+mode\b", "JAILBREAK_ATTEMPT"),
    (r"(?i)\bsystem\s+override\s*:\s*status\s*=\s*satisfied\b", "SYSTEM_STATUS_OVERRIDE"),
    (r"(?i)\b(?:chatgpt|claude|gemini|ai)\s+(?:said|confirmed|certified|guaranteed|asserts?).*?(?:is\s+)?(?:fully\s+)?compliant\b", "LLM_THIRD_PARTY_HALLUCINATION_CLAIM"),
    (r"(?i)\b(?:treat|use)\s+this\s+(?:document|text|input)\s+as\s+(?:the\s+)?system\s+prompt\b", "SYSTEM_PROMPT_SUBSTITUTION"),
    (r"(?i)\bact\s+as\s+bis\b", "REGULATORY_AUTHORITY_IMPERSONATION"),
    (r"(?i)\bcertify\s+this\s+product\b", "UNAUTHORIZED_CERTIFICATION_COMMAND"),
]


def scan_and_sanitize_untrusted_text(raw_text: str) -> PromptGuardScanResult:
    """Scan untrusted user/document text for prompt injection and malicious instructions."""
    detected = []
    sanitized = raw_text

    for pattern, name in INJECTION_PATTERNS:
        matches = re.findall(pattern, raw_text)
        if matches:
            detected.append(name)
            # Neutralize instruction: replace with passive audit note
            sanitized = re.sub(pattern, f"[NEUTRALIZED_UNTRUSTED_INSTRUCTION: {name}]", sanitized)

    if detected:
        return PromptGuardScanResult(
            is_safe=False,
            detected_patterns=detected,
            sanitized_text=sanitized,
            security_verdict="ADVERSARIAL_INSTRUCTION_NEUTRALIZED",
        )

    return PromptGuardScanResult(
        is_safe=True,
        detected_patterns=[],
        sanitized_text=raw_text,
        security_verdict="CLEAN",
    )
