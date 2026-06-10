import re

# Simple regex patterns for PII
EMAIL_REGEX = re.compile(r"[\w\.-]+@[\w\.-]+\.\w+")
# Indian phone numbers (+91) followed by 10 digits
PHONE_REGEX = re.compile(r"\b(?:\+91[-.\s]?)?[6-9]\d{9}\b")
# Aadhaar 12-digit format
AADHAAR_REGEX = re.compile(r"\b\d{4}\s?\d{4}\s?\d{4}\b")

def scrub_pii(text: str) -> str:
    """Removes emails, Indian phone numbers, and Aadhaar-like patterns."""
    if not text:
        return text
    text = EMAIL_REGEX.sub("[REDACTED]", text)
    text = PHONE_REGEX.sub("[REDACTED]", text)
    text = AADHAAR_REGEX.sub("[REDACTED]", text)
    return text
