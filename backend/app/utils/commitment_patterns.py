"""
commitment_patterns.py
----------------------
Regex-based patterns for detecting promises, commitments, and action items
inside email text.  All patterns are intentionally permissive — false positives
are cheaper than false negatives for a commitment tracker.
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional


# ---------------------------------------------------------------------------
# Pattern groups
# ---------------------------------------------------------------------------

# "I will / I'll / we will / we'll / I am going to …"
_FIRST_PERSON_PROMISE = re.compile(
    r"\b(i|we)\s+(will|'ll|am going to|are going to|shall|promise to|commit to|plan to|intend to)\s+"
    r"(?P<action>[^.!?\n]{5,120})",
    re.IGNORECASE,
)

# "I'll send / I'll share / I'll follow up …"
_WILL_VERB = re.compile(
    r"\b(i|we)\s*'?ll\s+(?P<action>[^.!?\n]{5,100})",
    re.IGNORECASE,
)

# "Please find / Please see / Please review …" — implicit commitment from sender
_PLEASE_ACTION = re.compile(
    r"\bplease\s+(?P<action>(?:find|see|review|check|confirm|let me know|revert|respond|reply|approve|sign|complete|fill)[^.!?\n]{0,80})",
    re.IGNORECASE,
)

# "I'll get back to you / I'll revert / Let me check and get back …"
_GET_BACK = re.compile(
    r"\b(i|we)\s*(will|'ll)?\s*(get\s*back|revert|follow[\s-]*up|circle[\s-]*back)\b[^.!?\n]{0,80}",
    re.IGNORECASE,
)

# Deadline phrases: "by Friday", "by end of day", "by 5 PM", "before the meeting"
_DEADLINE_PHRASE = re.compile(
    r"\b(by|before|due|no later than|not later than|until|till)\s+"
    r"(?P<deadline>"
    r"(?:monday|tuesday|wednesday|thursday|friday|saturday|sunday)"
    r"|(?:end\s+of\s+(?:day|week|month|quarter|year))"
    r"|(?:eod|eow|eom|eoq|eoy)"
    r"|(?:\d{1,2}[\/\-\.]\d{1,2}(?:[\/\-\.]\d{2,4})?)"   # dates like 12/31 or 31-12-2025
    r"|(?:\d{1,2}\s*(?:am|pm))"                             # times like 5 PM
    r"|(?:the\s+(?:meeting|call|standup|review|deadline|presentation|demo))"
    r"|(?:next\s+\w+)"                                      # "next Tuesday"
    r"|(?:this\s+\w+)"                                      # "this Friday"
    r"|(?:tomorrow|tonight|today)"
    r")",
    re.IGNORECASE,
)

# "Action required", "action item", "TODO", "to-do"
_ACTION_ITEM_MARKER = re.compile(
    r"\b(action\s+(required|item|needed)|todo|to[\s-]do|task\s+assigned|assigned\s+to)\b[^.!?\n]{0,80}",
    re.IGNORECASE,
)

# "Sending / Sharing / Attaching / Forwarding the …" (present-continuous commitment)
_PROGRESSIVE_SEND = re.compile(
    r"\b(sending|sharing|attaching|forwarding|uploading|submitting|delivering)\s+(?P<action>[^.!?\n]{5,80})",
    re.IGNORECASE,
)

# "You will receive / You should expect …" (commitment from sender to recipient)
_YOU_WILL_RECEIVE = re.compile(
    r"\byou\s+(will|should|can)\s+(?:receive|expect|get|find|see|have)\s+(?P<action>[^.!?\n]{5,80})",
    re.IGNORECASE,
)

ALL_PATTERNS = [
    ("first_person_promise", _FIRST_PERSON_PROMISE),
    ("will_verb",            _WILL_VERB),
    ("please_action",        _PLEASE_ACTION),
    ("get_back",             _GET_BACK),
    ("action_item_marker",   _ACTION_ITEM_MARKER),
    ("progressive_send",     _PROGRESSIVE_SEND),
    ("you_will_receive",     _YOU_WILL_RECEIVE),
]


# ---------------------------------------------------------------------------
# Data class
# ---------------------------------------------------------------------------

@dataclass
class ExtractedCommitment:
    raw_text: str                        # The full matched sentence / span
    action: str                          # Cleaned action description
    deadline: Optional[str] = None       # Deadline string if found nearby
    pattern_type: str = "unknown"        # Which pattern group matched
    confidence: float = 0.0             # Simple heuristic confidence 0-1
    sentence_index: int = 0             # Which sentence in the email


# ---------------------------------------------------------------------------
# Core extraction helpers
# ---------------------------------------------------------------------------

def _split_sentences(text: str) -> List[str]:
    """Naive sentence splitter — good enough for email bodies."""
    parts = re.split(r"(?<=[.!?])\s+|\n{2,}", text.strip())
    return [p.strip() for p in parts if len(p.strip()) > 4]


def _find_nearby_deadline(sentence: str) -> Optional[str]:
    m = _DEADLINE_PHRASE.search(sentence)
    return m.group("deadline").strip() if m else None


def _clean_action(raw: str) -> str:
    """Strip trailing punctuation and whitespace from an action snippet."""
    cleaned = raw.strip().rstrip(".,;:!? \t")
    # Truncate at first sentence boundary inside the action
    short = re.split(r"[.!?]", cleaned)[0].strip()
    return short if short else cleaned


def _compute_confidence(pattern_type: str, sentence: str, has_deadline: bool) -> float:
    """
    Very lightweight heuristic confidence score.
    A proper ML classifier could replace this later.
    """
    base = {
        "first_person_promise": 0.85,
        "will_verb":            0.80,
        "get_back":             0.75,
        "please_action":        0.65,
        "progressive_send":     0.70,
        "you_will_receive":     0.72,
        "action_item_marker":   0.78,
    }.get(pattern_type, 0.60)

    if has_deadline:
        base = min(1.0, base + 0.10)

    # Boost for explicit first-person pronoun
    if re.search(r"\b(i|we)\b", sentence, re.IGNORECASE):
        base = min(1.0, base + 0.05)

    return round(base, 2)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def extract_commitments(text: str, min_confidence: float = 0.50) -> List[ExtractedCommitment]:
    """
    Extract commitment candidates from raw email text.

    Parameters
    ----------
    text : str
        Raw (non-normalized) email body or combined subject+body.
    min_confidence : float
        Drop candidates whose heuristic confidence is below this value.

    Returns
    -------
    List[ExtractedCommitment]
        Deduplicated list ordered by sentence position.
    """
    sentences = _split_sentences(text)
    seen_actions: set = set()
    results: List[ExtractedCommitment] = []

    for idx, sentence in enumerate(sentences):
        for pattern_type, pattern in ALL_PATTERNS:
            match = pattern.search(sentence)
            if not match:
                continue

            # Pull action text from named group if available, else full match
            action_raw = match.groupdict().get("action") or match.group(0)
            action = _clean_action(action_raw)

            if not action or len(action) < 5:
                continue

            # Deduplicate by normalised action text
            action_key = re.sub(r"\s+", " ", action.lower())
            if action_key in seen_actions:
                continue
            seen_actions.add(action_key)

            deadline = _find_nearby_deadline(sentence)
            confidence = _compute_confidence(pattern_type, sentence, bool(deadline))

            if confidence < min_confidence:
                continue

            results.append(
                ExtractedCommitment(
                    raw_text=sentence,
                    action=action,
                    deadline=deadline,
                    pattern_type=pattern_type,
                    confidence=confidence,
                    sentence_index=idx,
                )
            )
            # Only take the first pattern match per sentence to avoid duplicates
            break

    return results
