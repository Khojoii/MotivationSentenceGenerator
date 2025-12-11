# Python standard libraries
import re
# internal modules
from logger import get_logger

logger = get_logger()

def force_json_closure(text: str) -> str:
    match = re.search(r"\{.*\}", text, re.S)
    if match:
        logger.debug("JSON closure detected in text")
        return match.group()
    logger.warning("No JSON object found in text, returning empty dict")
    return "{}"


def normalize_mixed_text(text: str) -> str:
    """
    Normalize mixed text by:
    1. Replacing multiple spaces/newlines with a single space
    2. Removing leading/trailing whitespace
    3. Removing non-printable characters
    """
    text = re.sub(r'[^\x20-\x7E\n]', '', text)
    text = re.sub(r'\s+', ' ', text)
    logger.debug("Text normalized using normalize_mixed_text")
    return text.strip()