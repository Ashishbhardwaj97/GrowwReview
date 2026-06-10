import re
import emoji
from langdetect import detect, LangDetectException

def normalise_text(text: str) -> str:
    """Lowercases and strips excessive whitespace."""
    if not text:
        return ""
    text = text.lower()
    # Replace multiple whitespaces/newlines with single space
    text = re.sub(r"\s+", " ", text)
    return text.strip()

def is_valid_review(text: str, min_length: int = 10) -> bool:
    """
    Checks if review meets minimum quality standards.
    Discards very short reviews and reviews that are mostly emojis/special chars.
    """
    if len(text) < min_length:
        return False
        
    # Heuristic: if stripping out all normal characters leaves more than 
    # half the length as emojis/weird symbols, discard it
    alphanumeric_count = sum(1 for c in text if c.isalnum() or c.isspace())
    if alphanumeric_count < len(text) * 0.5:
        return False
        
    # 1. Remove reviews with less than 8 words
    if len(text.split()) < 8:
        return False
        
    # 2. Remove reviews which have emojis
    if emoji.emoji_count(text) > 0:
        return False
        
    # 3. Remove reviews which are in another language (non-English)
    try:
        if detect(text) != 'en':
            return False
    except LangDetectException:
        return False
        
    return True
