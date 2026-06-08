"""
Decision tracker: identifies business decisions made during the meeting.
"""

import re
import json
import logging

logger = logging.getLogger(__name__)

# Sentence-level patterns indicating a decision was made
DECISION_PATTERNS = [
    # "Team agreed to migrate to AWS"
    r"([^.!?\n]*(?:[Tt]eam|[Ww]e|[Ee]veryone|[Aa]ll)\s+agreed\s+to\s+[^.!?\n]+[.!?]?)",
    # "Decision made to / Decision was made to"
    r"([^.!?\n]*[Dd]ecision\s+(?:was\s+)?made\s+to\s+[^.!?\n]+[.!?]?)",
    # "We decided to ..."
    r"([^.!?\n]*(?:[Ww]e|[Tt]eam|[Gg]roup)\s+decided\s+(?:to\s+)?[^.!?\n]+[.!?]?)",
    # "It was decided that ..."
    r"([^.!?\n]*[Ii]t\s+was\s+decided\s+that\s+[^.!?\n]+[.!?]?)",
    # "Agreed: / Agreement: ..."
    r"([^.!?\n]*[Aa]greed[:\s]+[^.!?\n]+[.!?]?)",
    # "We will go with ..."
    r"([^.!?\n]*(?:[Ww]e|[Tt]eam)\s+will\s+go\s+with\s+[^.!?\n]+[.!?]?)",
    # "Approved: ..."
    r"([^.!?\n]*[Aa]pproved[:\s]+[^.!?\n]+[.!?]?)",
    # "The team chose / selected"
    r"([^.!?\n]*(?:[Tt]eam|[Ww]e)\s+(?:chose|selected|picked|opted\s+for)\s+[^.!?\n]+[.!?]?)",
    # "Moving forward with ..."
    r"([^.!?\n]*[Mm]oving\s+forward\s+with\s+[^.!?\n]+[.!?]?)",
    # "Consensus reached: ..."
    r"([^.!?\n]*[Cc]onsensus\s+(?:was\s+)?reached\s+(?:that\s+|on\s+)?[^.!?\n]+[.!?]?)",
    # "Final decision: ..."
    r"([^.!?\n]*[Ff]inal\s+decision[:\s]+[^.!?\n]+[.!?]?)",
]


def _extract_context(transcript: str, decision_text: str, window: int = 200) -> str:
    """
    Extract a surrounding context snippet for a detected decision.
    Looks for the decision text in the transcript and returns nearby text.
    """
    pos = transcript.find(decision_text[:40])
    if pos == -1:
        return ""
    start = max(0, pos - window // 2)
    end = min(len(transcript), pos + len(decision_text) + window // 2)
    snippet = transcript[start:end].strip()
    # Truncate neatly at sentence boundary
    snippet = re.sub(r"\s+", " ", snippet)
    return snippet[:300]


def _clean_decision(raw: str) -> str:
    """Normalize whitespace and trim the decision text."""
    text = re.sub(r"\s+", " ", raw).strip().rstrip(".,;:")
    if text:
        text = text[0].upper() + text[1:]
    return text


def extract_decisions(transcript: str) -> list[dict]:
    """
    Parse the transcript and return a list of decision dicts.

    Each dict has:
        decision – the decision statement
        context  – surrounding text for additional context
    """
    decisions: list[dict] = []
    seen: set[str] = set()

    for pattern in DECISION_PATTERNS:
        for match in re.finditer(pattern, transcript):
            raw = match.group(1)
            decision = _clean_decision(raw)

            if not decision or len(decision) < 10:
                continue

            dedup_key = decision.lower()[:60]
            if dedup_key in seen:
                continue

            seen.add(dedup_key)
            context = _extract_context(transcript, raw)

            decisions.append({"decision": decision, "context": context})

    return decisions


def decisions_to_json(decisions: list[dict]) -> str:
    """Serialize decisions list to JSON string for DB storage."""
    return json.dumps(decisions, ensure_ascii=False)


def decisions_from_json(json_str: str) -> list[dict]:
    """Deserialize decisions from JSON string."""
    if not json_str:
        return []
    try:
        return json.loads(json_str)
    except json.JSONDecodeError:
        return []
