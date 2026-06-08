"""
Deadline detector: extracts dates, due dates, and time-bound commitments
from meeting transcripts.
"""

import re
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# Named day patterns
NAMED_DAYS = r"(?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)"
# Named month patterns
NAMED_MONTHS = (
    r"(?:January|February|March|April|May|June|July|August|"
    r"September|October|November|December|"
    r"Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sep|Oct|Nov|Dec)"
)
# Relative time expressions
RELATIVE_TIME = r"(?:next\s+week|end\s+of\s+(?:the\s+)?(?:week|month|quarter|year)|by\s+EOD|by\s+COB|by\s+EOM|this\s+(?:week|month|quarter|Friday|Monday))"

# Core deadline trigger verbs/phrases
DEADLINE_TRIGGERS = (
    r"(?:by|before|due|submit(?:ted)?\s+by|complete(?:d)?\s+by|"
    r"deliver(?:ed)?\s+by|finish(?:ed)?\s+by|launch(?:ed)?\s+(?:on|by)|"
    r"release(?:d)?\s+(?:on|by)|deploy(?:ed)?\s+(?:on|by)|"
    r"deadline[:\s]+|due\s+date[:\s]+|target\s+date[:\s]+)"
)

# Full deadline detection patterns
DEADLINE_PATTERNS = [
    # "Submit by Friday" / "Due by Monday"
    rf"([^.!?\n]{{0,60}}{DEADLINE_TRIGGERS}\s*{NAMED_DAYS}[^.!?\n]{{0,80}})",
    # "Submit by July 20" / "Launch on March 15th"
    rf"([^.!?\n]{{0,60}}{DEADLINE_TRIGGERS}\s*{NAMED_MONTHS}\s*\d{{1,2}}(?:st|nd|rd|th)?(?:\s*,?\s*\d{{4}})?[^.!?\n]{{0,80}})",
    # "Submit by 20 July 2025"
    rf"([^.!?\n]{{0,60}}{DEADLINE_TRIGGERS}\s*\d{{1,2}}\s*{NAMED_MONTHS}(?:\s*\d{{4}})?[^.!?\n]{{0,80}})",
    # "Submit by 2025-07-20" or "2025/07/20"
    rf"([^.!?\n]{{0,60}}{DEADLINE_TRIGGERS}\s*\d{{4}}[-/]\d{{1,2}}[-/]\d{{1,2}}[^.!?\n]{{0,80}})",
    # Relative time: "finish by end of month" / "done by next week"
    rf"([^.!?\n]{{0,60}}{DEADLINE_TRIGGERS}\s*{RELATIVE_TIME}[^.!?\n]{{0,80}})",
    # "Q2 deadline" / "Q3 launch"
    r"([^.!?\n]{0,60}Q[1-4]\s*(?:deadline|launch|release|delivery|target)[^.!?\n]{0,80})",
    # Direct date mentions with context
    rf"([^.!?\n]{{0,60}}(?:target|milestone|checkpoint)[:\s]+{NAMED_MONTHS}\s*\d{{1,2}}[^.!?\n]{{0,80}})",
]


def _extract_date_string(text: str) -> str:
    """
    Try to pull a recognizable date/time reference out of a deadline sentence.
    Returns the best date substring found, or "TBD".
    """
    # Named month + day
    m = re.search(
        rf"({NAMED_MONTHS}\s+\d{{1,2}}(?:st|nd|rd|th)?(?:\s*,?\s*\d{{4}})?)",
        text, re.IGNORECASE
    )
    if m:
        return m.group(1).strip()

    # Day number + named month
    m = re.search(
        rf"(\d{{1,2}}(?:st|nd|rd|th)?\s+{NAMED_MONTHS}(?:\s+\d{{4}})?)",
        text, re.IGNORECASE
    )
    if m:
        return m.group(1).strip()

    # ISO date
    m = re.search(r"(\d{4}[-/]\d{1,2}[-/]\d{1,2})", text)
    if m:
        return m.group(1).strip()

    # Named day
    m = re.search(rf"({NAMED_DAYS})", text, re.IGNORECASE)
    if m:
        return m.group(1).strip()

    # Relative
    m = re.search(
        r"(end of (?:the )?(?:week|month|quarter|year)|next week|by EOD|by COB|by EOM|Q[1-4])",
        text, re.IGNORECASE
    )
    if m:
        return m.group(1).strip()

    return "TBD"


def _clean_deadline_text(raw: str) -> str:
    """Normalize whitespace and capitalize."""
    text = re.sub(r"\s+", " ", raw).strip().rstrip(".,;:")
    if text:
        text = text[0].upper() + text[1:]
    return text


def extract_deadlines(transcript: str) -> list[dict]:
    """
    Parse the transcript and return a list of deadline dicts.

    Each dict has:
        deadline – full deadline statement
        date     – extracted date/time reference string
    """
    deadlines: list[dict] = []
    seen: set[str] = set()

    for pattern in DEADLINE_PATTERNS:
        for match in re.finditer(pattern, transcript, re.IGNORECASE):
            raw = match.group(1)
            deadline_text = _clean_deadline_text(raw)

            if not deadline_text or len(deadline_text) < 8:
                continue

            dedup_key = deadline_text.lower()[:60]
            if dedup_key in seen:
                continue

            seen.add(dedup_key)
            date_str = _extract_date_string(deadline_text)

            deadlines.append({"deadline": deadline_text, "date": date_str})

    return deadlines


def deadlines_to_json(deadlines: list[dict]) -> str:
    """Serialize deadlines list to JSON string for DB storage."""
    return json.dumps(deadlines, ensure_ascii=False)


def deadlines_from_json(json_str: str) -> list[dict]:
    """Deserialize deadlines from JSON string."""
    if not json_str:
        return []
    try:
        return json.loads(json_str)
    except json.JSONDecodeError:
        return []
