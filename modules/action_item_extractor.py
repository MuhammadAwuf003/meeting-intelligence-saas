"""
Action item extractor: detects task assignments from meeting transcripts.
Uses pattern matching and NLP heuristics to identify who owns what task.
"""

import re
import json
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Patterns that indicate a task or assignment
ACTION_PATTERNS = [
    # "John will send the report"
    r"([A-Z][a-z]+(?:\s[A-Z][a-z]+)?)\s+will\s+([^.!?\n]+[.!?]?)",
    # "John to update the dashboard"
    r"([A-Z][a-z]+(?:\s[A-Z][a-z]+)?)\s+to\s+((?:update|send|create|review|complete|submit|prepare|build|schedule|contact|follow|reach|check|finalize|present|share|write|fix|test|deploy|implement|coordinate|organize|draft|confirm)[^.!?\n]+[.!?]?)",
    # "Action item: John - update the report"
    r"[Aa]ction\s+[Ii]tem[:\s]+([A-Z][a-z]+(?:\s[A-Z][a-z]+)?)\s*[-–:]\s*([^.!?\n]+[.!?]?)",
    # "Assigned to John: review the mockups"
    r"[Aa]ssigned\s+to\s+([A-Z][a-z]+(?:\s[A-Z][a-z]+)?)[:\s]+([^.!?\n]+[.!?]?)",
    # "John is responsible for ..."
    r"([A-Z][a-z]+(?:\s[A-Z][a-z]+)?)\s+is\s+responsible\s+for\s+([^.!?\n]+[.!?]?)",
    # "John needs to ..."
    r"([A-Z][a-z]+(?:\s[A-Z][a-z]+)?)\s+needs?\s+to\s+([^.!?\n]+[.!?]?)",
    # "John should ..."
    r"([A-Z][a-z]+(?:\s[A-Z][a-z]+)?)\s+should\s+((?:update|send|create|review|complete|submit|prepare|build|schedule|contact|follow|reach|check|finalize|present|share|write|fix|test|deploy|implement)[^.!?\n]+[.!?]?)",
    # "Let's have John handle ..."
    r"[Ll]et(?:'s|s)?\s+have\s+([A-Z][a-z]+(?:\s[A-Z][a-z]+)?)\s+(?:handle\s+|work\s+on\s+|take\s+care\s+of\s+)?([^.!?\n]+[.!?]?)",
]

# Generic (no assignee) task patterns
GENERIC_TASK_PATTERNS = [
    r"(?:[Ww]e need to|[Ww]e should|[Tt]eam (?:should|will|needs? to))\s+([^.!?\n]+[.!?]?)",
    r"(?:[Tt]o[- ]do|TODO)[:\s]+([^.!?\n]+[.!?]?)",
    r"(?:[Nn]ext step|[Ff]ollow[- ]up)[:\s]+([^.!?\n]+[.!?]?)",
]

# Common non-person capitalized words to skip
NON_PERSON_WORDS = {
    "The", "This", "That", "We", "They", "It", "Our", "Their", "His", "Her",
    "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday",
    "January", "February", "March", "April", "May", "June", "July", "August",
    "September", "October", "November", "December", "Q1", "Q2", "Q3", "Q4",
    "Team", "Meeting", "Company", "Project", "System", "Platform", "Service",
    "Please", "Also", "However", "Therefore", "Meanwhile", "Additionally",
}


def _is_likely_person(name: str) -> bool:
    """Heuristic: is this token likely a person's name?"""
    parts = name.strip().split()
    if not parts:
        return False
    first = parts[0]
    if first in NON_PERSON_WORDS:
        return False
    if len(first) < 2:
        return False
    return True


def _clean_task(task: str) -> str:
    """Strip trailing punctuation noise and normalize whitespace."""
    task = re.sub(r"\s+", " ", task).strip()
    task = task.rstrip(".,;:")
    # Capitalize first letter
    if task:
        task = task[0].upper() + task[1:]
    return task


def extract_action_items(transcript: str) -> list[dict]:
    """
    Parse the transcript and return a list of action item dicts.

    Each dict has:
        person – assignee name (or "Team" for generic tasks)
        task   – task description
    """
    items: list[dict] = []
    seen: set[str] = set()

    for pattern in ACTION_PATTERNS:
        for match in re.finditer(pattern, transcript):
            person = match.group(1).strip()
            task = match.group(2).strip()

            if not _is_likely_person(person):
                continue

            task = _clean_task(task)
            dedup_key = f"{person.lower()}|{task.lower()[:40]}"

            if dedup_key not in seen and len(task) > 5:
                seen.add(dedup_key)
                items.append({"person": person, "task": task})

    # Generic team tasks
    for pattern in GENERIC_TASK_PATTERNS:
        for match in re.finditer(pattern, transcript):
            task = _clean_task(match.group(1).strip())
            dedup_key = f"team|{task.lower()[:40]}"
            if dedup_key not in seen and len(task) > 5:
                seen.add(dedup_key)
                items.append({"person": "Team", "task": task})

    return items


def action_items_to_json(items: list[dict]) -> str:
    """Serialize action items list to JSON string for DB storage."""
    return json.dumps(items, ensure_ascii=False)


def action_items_from_json(json_str: str) -> list[dict]:
    """Deserialize action items from JSON string."""
    if not json_str:
        return []
    try:
        return json.loads(json_str)
    except json.JSONDecodeError:
        return []
