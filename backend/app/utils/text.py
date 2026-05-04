import re


MONEY_PATTERN = re.compile(
    r"(?:\$|usd|inr|eur|gbp|invoice|payment|amount|balance|refund|salary|budget)",
    re.IGNORECASE,
)
DEADLINE_PATTERN = re.compile(
    r"(?:\b(?:today|tomorrow|tonight|urgent|asap|immediately)\b|\bby\b\s+\d|\bdue\b|\bdeadline\b|\beod\b|\bwithin\s+\d+)",
    re.IGNORECASE,
)


def normalize_text(value: str) -> str:
    text = str(value or "").replace("\r", " ").replace("\n", " ")
    text = re.sub(r"https?://\S+|www\.\S+", " URL ", text, flags=re.IGNORECASE)
    text = re.sub(r"\S+@\S+", " EMAIL ", text)
    text = re.sub(r"[^a-zA-Z0-9$%!?.,:/\\-]+", " ", text)
    text = re.sub(r"\s+", " ", text).strip().lower()
    return text


def combine_subject_body(subject: str, body: str) -> str:
    return f"{subject or ''} {body or ''}".strip()


def detect_contains_money(text: str) -> int:
    return int(bool(MONEY_PATTERN.search(text)))


def detect_contains_deadline(text: str) -> int:
    return int(bool(DEADLINE_PATTERN.search(text)))
