from __future__ import annotations

import html
import json
import random
import re
import shutil
from collections import Counter
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


SEED = 42
random.seed(SEED)
np.random.seed(SEED)
sns.set_theme(style="whitegrid")

BASE = Path(r"C:\Users\mbmeg\Desktop\replynt_v2")
FINAL = BASE / "data" / "final"
NOTEBOOK = BASE / "notebooks" / "03_final_data_polish.ipynb"
SOURCE = FINAL / "triage_train_v2.csv"
BACKUP = FINAL / "triage_train_v2_backup.csv"
OUTPUT = FINAL / "triage_train_final.csv"

DEADLINE_RE = re.compile(
    r"\b(?:due|deadline|today|tomorrow|asap|urgent|immediately|by eod|by cob|this friday|next week|when convenient)\b",
    re.I,
)
MONEY_RE = re.compile(
    r"(?:\$|usd|eur|gbp|inr|\binvoice\b|\bpayment\b|\bamount\b|\bpricing\b|\bquote\b|\bproposal\b)",
    re.I,
)
QUESTION_RE = re.compile(r"\?")

P3_YES_INTENTS = [
    "Follow Up",
    "Meeting Request",
    "Complaint",
    "Quote Request",
    "Support Request",
]
MIN_INTENT_ROWS = 500

NEEDS_REPLY = {
    "Complaint": "Yes",
    "Follow Up": "Yes",
    "Meeting Request": "Yes",
    "Payment Reminder": "Yes",
    "Sales Outreach": "Yes",
    "Quote Request": "Yes",
    "Interview Request": "Yes",
    "Investor Interest": "Yes",
    "Internal FYI": "No",
    "Newsletter": "No",
    "Product Update": "No",
    "Support Request": "Yes",
}

FIRST_NAMES = [
    "Alex", "Sam", "Jordan", "Taylor", "Morgan", "Casey", "Riley", "Avery", "Drew", "Cameron",
    "Jamie", "Parker", "Quinn", "Reese", "Hayden", "Robin", "Blake", "Rowan", "Kendall", "Skyler",
]
COMPANIES = [
    "Northstar Labs", "BluePeak Systems", "Harbor Finance", "Summit Retail", "Aster Health",
    "Brightline Logistics", "Cedar Analytics", "Maple Ridge Foods", "Vertex Cloud", "Cobalt Energy",
]
TOPICS = [
    "the previous proposal", "last week's note", "the rollout plan", "the invoice draft", "the support summary",
    "the onboarding checklist", "the latest timeline", "the budget review", "the open ticket", "the draft quote",
]
ISSUES = [
    "a small formatting issue in the invoice", "a minor display issue in the dashboard", "an intermittent export mismatch",
    "a small typo in the generated report", "a light workflow issue in the approval screen", "a minor issue with the attachment naming",
]
TIMES = ["next Tuesday afternoon", "sometime next week", "later this week", "whenever convenient", "early next week"]


def clean_text(value: object) -> str:
    if pd.isna(value):
        return ""
    text = html.unescape(str(value))
    text = re.sub(r"<[^>]+>", " ", text)
    text = text.replace("\\n", " ").replace("\\r", " ").replace("\\t", " ")
    text = text.replace("\n", " ").replace("\r", " ").replace("\t", " ")
    text = re.sub(r"[^\x20-\x7E]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def recalc_features(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["subject"] = out["subject"].fillna("").map(clean_text).replace("", "(no subject)")
    out["body"] = out["body"].fillna("").map(clean_text).replace("", "(no body)")
    out["priority"] = out["priority"].fillna("P2").astype(str).str.strip()
    out["intent"] = out["intent"].astype(str).str.strip()
    out["needs_reply"] = out["intent"].map(NEEDS_REPLY).fillna(out["needs_reply"].astype(str).str.strip())
    out["combined_text"] = (out["subject"] + " " + out["body"]).str.replace(r"\s+", " ", regex=True).str.strip()
    out["word_count"] = out["combined_text"].str.findall(r"\b\w+\b").str.len()
    out["subject_length"] = out["subject"].str.len()
    out["body_length"] = out["body"].str.len()
    out["contains_deadline"] = out["combined_text"].str.contains(DEADLINE_RE, regex=True)
    out["contains_money"] = out["combined_text"].str.contains(MONEY_RE, regex=True)
    out["contains_question"] = out["combined_text"].str.contains(QUESTION_RE, regex=True)
    out = out[out["word_count"] >= 5].copy()
    cols = [
        "subject",
        "body",
        "priority",
        "intent",
        "needs_reply",
        "combined_text",
        "word_count",
        "subject_length",
        "body_length",
        "contains_deadline",
        "contains_money",
        "contains_question",
    ]
    return out[cols].reset_index(drop=True)


def inspect_dataset(df: pd.DataFrame, title: str) -> None:
    print(title)
    print("shape:", df.shape)
    print("columns:", df.columns.tolist())
    print("null counts:")
    print(df.isna().sum())
    print("duplicate exact rows:", df.duplicated().sum())
    print("duplicate bodies:", int(df.duplicated(subset=["body"]).sum()))


def resolve_body_duplicates(df: pd.DataFrame) -> tuple[pd.DataFrame, int, int]:
    retained = []
    rows_removed = 0
    rows_retained = 0

    for _, group in df.groupby("body", sort=False, dropna=False):
        group = group.copy()
        if len(group) == 1:
            retained.append(group.iloc[[0]])
            rows_retained += 1
            continue

        labels = list(group[["priority", "intent", "needs_reply"]].itertuples(index=False, name=None))
        combo_counts = Counter(labels)

        if len(combo_counts) > 1:
            majority_count = max(combo_counts.values())
            majority = next(label for label in labels if combo_counts[label] == majority_count)
            winner = group[
                (group["priority"] == majority[0])
                & (group["intent"] == majority[1])
                & (group["needs_reply"] == majority[2])
            ].iloc[[0]]
            retained.append(winner)
            rows_retained += 1
            rows_removed += len(group) - 1
        else:
            keep_n = min(2, len(group))
            kept = group.iloc[:keep_n]
            retained.append(kept)
            rows_retained += len(kept)
            rows_removed += len(group) - keep_n

    cleaned = pd.concat(retained, ignore_index=True)
    return cleaned, rows_removed, rows_retained


def synth_row(intent: str, idx: int, rng: random.Random) -> dict[str, str]:
    name = rng.choice(FIRST_NAMES)
    company = rng.choice(COMPANIES)
    topic = rng.choice(TOPICS)
    issue = rng.choice(ISSUES)
    time_phrase = rng.choice(TIMES)

    templates = {
        "Follow Up": (
            [
                "gentle follow up on previous note",
                "checking in when you have a moment",
                "quick follow up on the open item",
                "light follow up on our last message",
            ],
            [
                f"Hi {name}, just checking if you had a chance to review {topic}. Please reply when convenient.",
                f"Hello {name}, following up on {topic}. There is no rush, but a short update would be helpful when you have time.",
                f"Hi {name}, I wanted to gently follow up on {topic}. Let me know when convenient if there is any progress to share.",
            ],
        ),
        "Meeting Request": (
            [
                "optional meeting next week",
                "open to a short meeting if useful",
                "would a light check-in be helpful?",
                "meeting request for a convenient time",
            ],
            [
                f"Hello {name}, if helpful, we could schedule a short meeting {time_phrase} to review {topic}. Please let me know what works for you.",
                f"Hi {name}, there is no urgency, but I would be glad to meet {time_phrase} if you would like to discuss {topic}.",
                f"Hello {name}, let me know if you would still like to meet {time_phrase}. I am happy to work around your schedule.",
            ],
        ),
        "Complaint": (
            [
                "minor issue with invoice formatting",
                "small concern on the latest document",
                "light complaint about a recent detail",
                "small issue for review when convenient",
            ],
            [
                f"Hello team, there is {issue}. It is not urgent, but please review it when convenient and let me know if a correction will be made.",
                f"Hi support, I noticed {issue} in the latest file from {company}. Please take a look when you have time.",
                f"Hello, I wanted to flag {issue}. The issue is minor, but I would appreciate a quick confirmation after your review.",
            ],
        ),
        "Quote Request": (
            [
                "quote clarification request",
                "small pricing question on the proposal",
                "quick clarification on one line item",
                "proposal detail to confirm",
            ],
            [
                f"Hi {name}, could you clarify one line item in the proposal for {company} when you have time? I just want to confirm the pricing detail.",
                f"Hello {name}, I have a small question about the quote attached to {topic}. Please clarify the line item when convenient.",
                f"Hi {name}, when you have a moment, could you confirm one pricing detail in the latest quote? That will help us close out the review.",
            ],
        ),
        "Support Request": (
            [
                "small support question when convenient",
                "minor issue for the support team",
                "quick help request on a low-priority item",
                "support follow-up for a small issue",
            ],
            [
                f"Hello support, I noticed {issue} in the {company} workflow. There is no urgency, but please review it when convenient.",
                f"Hi team, I have a small support request related to {topic}. Please take a look when you have time and let me know the best fix.",
                f"Hello support, there is a low-priority issue with the current setup. A response when convenient would be appreciated.",
            ],
        ),
    }

    subjects, bodies = templates[intent]
    subject = rng.choice(subjects)
    body = rng.choice(bodies)
    return {
        "subject": subject,
        "body": body,
        "priority": "P3",
        "intent": intent,
        "needs_reply": "Yes",
    }


def synth_balance_row(intent: str, idx: int, rng: random.Random) -> dict[str, str]:
    name = rng.choice(FIRST_NAMES)
    company = rng.choice(COMPANIES)
    topic = rng.choice(TOPICS)
    issue = rng.choice(ISSUES)
    time_phrase = rng.choice(TIMES)

    templates = {
        "Newsletter": (
            ["monthly product roundup", "customer newsletter for this month", "community update from the team", "newsletter: practical workflow ideas"],
            [
                f"Hello readers, this month's newsletter includes practical ideas for teams at {company}, a few customer highlights, and a short update on {topic}.",
                f"Hi there, here is our latest newsletter with customer stories, workflow notes, and a quick team update for the month.",
                f"Hello everyone, this edition covers helpful updates, a few launch notes, and practical guidance related to {topic}.",
            ],
            "P3",
            "No",
        ),
        "Internal FYI": (
            ["fyi for the internal team", "quick internal note", "visibility update for the team", "internal update for planning"],
            [
                f"Hello team, sharing this for visibility only. The latest note is about {topic}, and no action is needed right now.",
                f"Hi all, quick internal FYI that the team at {company} has updated the plan around {topic}.",
                f"Hello everyone, this is a simple internal note so the group has context before the next review.",
            ],
            "P3",
            "No",
        ),
        "Product Update": (
            ["product update for this week", "release note summary", "platform update from the team", "latest product improvements"],
            [
                f"Hello {name}, we released a product update related to {topic}. No action is required, but we wanted to share the latest improvements.",
                f"Hi team, this update includes a few product improvements and reliability fixes for teams using the platform at {company}.",
                f"Hello, sharing a quick product update with a few workflow improvements and minor fixes from this week's release.",
            ],
            "P3",
            "No",
        ),
        "Quote Request": (
            ["request for a refreshed quote", "pricing follow-up for review", "quote detail request", "budget quote request"],
            [
                f"Hi {name}, please send an updated quote for {company} when convenient so we can complete the review.",
                f"Hello {name}, we would appreciate a pricing quote tied to {topic}. Please send it over when you have time.",
                f"Hi team, we are looking for a quote with a little more detail on the proposed scope and pricing.",
            ],
            "P2",
            "Yes",
        ),
        "Follow Up": (
            ["follow up on the previous message", "checking in on an open item", "small follow-up request", "quick status follow-up"],
            [
                f"Hi {name}, I wanted to follow up on {topic}. Please send a short update when convenient.",
                f"Hello {name}, checking in on the open item from our last note. A quick reply would be appreciated.",
                f"Hi team, just following up to see whether there is any progress to share on {topic}.",
            ],
            "P2",
            "Yes",
        ),
        "Meeting Request": (
            ["schedule a short meeting", "meeting request for next week", "time to review the open item", "short discussion request"],
            [
                f"Hello {name}, would you be open to a short meeting {time_phrase} to discuss {topic}?",
                f"Hi {name}, please let me know if a brief meeting {time_phrase} would be useful for the next step.",
                f"Hello team, I would like to schedule a short meeting to review the open points around {topic}.",
            ],
            "P2",
            "Yes",
        ),
        "Complaint": (
            ["service issue for review", "customer concern about a recent issue", "problem reported by the team", "small complaint to review"],
            [
                f"Hello, I want to report {issue}. Please review it and let us know what correction you recommend.",
                f"Hi support, the team noticed {issue} and would appreciate a response on the next step.",
                f"Hello team, this issue is affecting our workflow and we would like someone to review it soon.",
            ],
            "P1",
            "Yes",
        ),
        "Support Request": (
            ["support request for review", "help needed on an open issue", "technical question from the team", "support follow-up request"],
            [
                f"Hello support, we need help reviewing {issue}. Please let us know the best next step.",
                f"Hi team, could someone take a look at {topic} and suggest the most practical fix?",
                f"Hello support, there is an open issue in the workflow and a short response would help the team move forward.",
            ],
            "P2",
            "Yes",
        ),
        "Sales Outreach": (
            ["idea to improve a workflow", "short intro if helpful", "supporting teams like yours", "note on process improvement"],
            [
                f"Hello {name}, we help teams like {company} simplify busy workflows and improve visibility. Let me know if a short intro would be useful.",
                f"Hi {name}, I thought our approach to workflow automation might be relevant to your team. I would be happy to share a quick overview.",
                f"Hello, reaching out because we support teams that want a more organized way to manage incoming work and follow-ups.",
            ],
            "P2",
            "Yes",
        ),
        "Investor Interest": (
            ["investor introduction note", "interest in learning more", "open to a brief conversation", "follow-up on company progress"],
            [
                f"Hello {name}, I have been following {company} and would be glad to schedule a short introductory conversation when convenient.",
                f"Hi {name}, I would welcome a chance to learn more about your progress and current priorities.",
                f"Hello, if helpful, I would be glad to connect and hear more about the team's direction over the coming months.",
            ],
            "P2",
            "Yes",
        ),
        "Interview Request": (
            ["interview scheduling request", "availability for an interview", "next interview step", "time to meet with the hiring team"],
            [
                f"Hello {name}, we would like to schedule an interview and would appreciate your availability for {time_phrase}.",
                f"Hi {name}, please let us know if you are open to a short interview conversation next week.",
                f"Hello, the hiring team would like to set up the next discussion when convenient for you.",
            ],
            "P2",
            "Yes",
        ),
        "Payment Reminder": (
            ["friendly payment reminder", "invoice still open", "reminder on the outstanding balance", "payment follow-up note"],
            [
                f"Hello {name}, this is a reminder that the invoice for {company} is still open. Please confirm the expected payment timing.",
                f"Hi {name}, we are following up on an outstanding balance and would appreciate a quick update.",
                f"Hello, please let us know if payment is already in process or if any clarification is needed from our side.",
            ],
            "P1",
            "Yes",
        ),
    }

    subjects, bodies, priority, needs_reply = templates[intent]
    return {
        "subject": rng.choice(subjects),
        "body": rng.choice(bodies),
        "priority": priority,
        "intent": intent,
        "needs_reply": needs_reply,
    }


def build_synthetic_p3_yes(existing: pd.DataFrame, n_rows: int = 150) -> pd.DataFrame:
    rng = random.Random(SEED)
    rows = []
    seen = set(zip(existing["subject"], existing["body"], existing["intent"], existing["priority"], existing["needs_reply"]))
    counts = {intent: 0 for intent in P3_YES_INTENTS}
    per_intent = n_rows // len(P3_YES_INTENTS)
    targets = {intent: per_intent for intent in P3_YES_INTENTS}
    for intent in P3_YES_INTENTS[: n_rows % len(P3_YES_INTENTS)]:
        targets[intent] += 1

    for intent in P3_YES_INTENTS:
        idx = 0
        while counts[intent] < targets[intent]:
            row = synth_row(intent, idx, rng)
            key = (clean_text(row["subject"]), clean_text(row["body"]), row["intent"], row["priority"], row["needs_reply"])
            idx += 1
            if key in seen:
                continue
            row["subject"] = clean_text(row["subject"])
            row["body"] = clean_text(row["body"])
            rows.append(row)
            seen.add(key)
            counts[intent] += 1
    return pd.DataFrame(rows)


def top_up_low_intents(existing: pd.DataFrame, min_rows: int = MIN_INTENT_ROWS) -> pd.DataFrame:
    rng = random.Random(SEED + 7)
    rows = []
    seen = set(zip(existing["subject"], existing["body"], existing["intent"], existing["priority"], existing["needs_reply"]))
    counts = existing["intent"].value_counts().to_dict()

    for intent, current in counts.items():
        target = max(current, min_rows)
        idx = 0
        while counts.get(intent, 0) < target:
            row = synth_balance_row(intent, idx, rng)
            key = (clean_text(row["subject"]), clean_text(row["body"]), row["intent"], row["priority"], row["needs_reply"])
            idx += 1
            if key in seen:
                continue
            row["subject"] = clean_text(row["subject"])
            row["body"] = clean_text(row["body"])
            rows.append(row)
            seen.add(key)
            counts[intent] = counts.get(intent, 0) + 1
    return pd.DataFrame(rows)


def conflicting_body_count(df: pd.DataFrame) -> int:
    count = 0
    for _, group in df.groupby("body", dropna=False):
        if len(group) <= 1:
            continue
        if len(group[["priority", "intent", "needs_reply"]].drop_duplicates()) > 1:
            count += 1
    return count


def print_final_quality(df: pd.DataFrame) -> None:
    print("final shape:", df.shape)
    print("\nnull counts:")
    print(df.isna().sum())
    print("\nduplicate exact rows:", df.duplicated().sum())
    print("\nduplicate bodies remaining:", int(df.duplicated(subset=["body"]).sum()))
    print("\nconflicting duplicate bodies remaining:", conflicting_body_count(df))
    print("\npriority distribution:")
    print(df["priority"].value_counts().sort_index())
    print("\nintent distribution:")
    print(df["intent"].value_counts().sort_index())
    print("\nneeds_reply distribution:")
    print(df["needs_reply"].value_counts().sort_index())
    print("\nsample rows:")
    print(df.head(10).to_string(index=False))


def make_charts(df: pd.DataFrame) -> None:
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))

    sns.countplot(data=df, x="priority", order=["P1", "P2", "P3"], ax=axes[0, 0], palette="crest")
    axes[0, 0].set_title("Priority Distribution")
    axes[0, 0].set_xlabel("Priority")

    sns.countplot(data=df, y="intent", order=df["intent"].value_counts().index, ax=axes[0, 1], palette="flare")
    axes[0, 1].set_title("Intent Distribution")
    axes[0, 1].set_xlabel("Rows")
    axes[0, 1].set_ylabel("")

    sns.countplot(data=df, x="needs_reply", order=["Yes", "No"], ax=axes[1, 0], palette="mako")
    axes[1, 0].set_title("Needs Reply Distribution")
    axes[1, 0].set_xlabel("Needs Reply")

    sns.histplot(data=df, x="word_count", bins=30, ax=axes[1, 1], color="#2A9D8F")
    axes[1, 1].set_title("Word Count Histogram")
    axes[1, 1].set_xlabel("Word Count")

    plt.tight_layout()
    plt.show()


def build_notebook() -> None:
    cells = []

    def md(text: str) -> None:
        cells.append({"cell_type": "markdown", "metadata": {}, "source": [line + "\n" for line in text.strip("\n").splitlines()]})

    def code(text: str) -> None:
        cells.append({"cell_type": "code", "metadata": {}, "execution_count": None, "outputs": [], "source": [line + "\n" for line in text.strip("\n").splitlines()]})

    md("# REPLYNT Final Triage Polish\n\nFinal cleanup pass for `triage_train_v2.csv` before model training.")
    md("## 1. Imports")
    code(
        """
from __future__ import annotations

import html
import random
import re
import shutil
from collections import Counter
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

SEED = 42
random.seed(SEED)
np.random.seed(SEED)
sns.set_theme(style="whitegrid")
"""
    )
    md("## 2. Paths, Labels, and Helpers")
    code(
        f"""
BASE = Path(r"{BASE}")
FINAL = BASE / "data" / "final"
SOURCE = FINAL / "triage_train_v2.csv"
BACKUP = FINAL / "triage_train_v2_backup.csv"
OUTPUT = FINAL / "triage_train_final.csv"

DEADLINE_RE = re.compile(r"\\b(?:due|deadline|today|tomorrow|asap|urgent|immediately|by eod|by cob|this friday|next week|when convenient)\\b", re.I)
MONEY_RE = re.compile(r"(?:\\$|usd|eur|gbp|inr|\\binvoice\\b|\\bpayment\\b|\\bamount\\b|\\bpricing\\b|\\bquote\\b|\\bproposal\\b)", re.I)
QUESTION_RE = re.compile(r"\\?")

P3_YES_INTENTS = {json.dumps(P3_YES_INTENTS)}
MIN_INTENT_ROWS = {MIN_INTENT_ROWS}
NEEDS_REPLY = {json.dumps(NEEDS_REPLY, indent=4)}
FIRST_NAMES = {json.dumps(FIRST_NAMES)}
COMPANIES = {json.dumps(COMPANIES)}
TOPICS = {json.dumps(TOPICS)}
ISSUES = {json.dumps(ISSUES)}
TIMES = {json.dumps(TIMES)}

def clean_text(value):
    if pd.isna(value):
        return ""
    text = html.unescape(str(value))
    text = re.sub(r"<[^>]+>", " ", text)
    text = text.replace("\\\\n", " ").replace("\\\\r", " ").replace("\\\\t", " ")
    text = text.replace("\\n", " ").replace("\\r", " ").replace("\\t", " ")
    text = re.sub(r"[^\\x20-\\x7E]", " ", text)
    text = re.sub(r"\\s+", " ", text).strip()
    return text

def recalc_features(df):
    out = df.copy()
    out["subject"] = out["subject"].fillna("").map(clean_text).replace("", "(no subject)")
    out["body"] = out["body"].fillna("").map(clean_text).replace("", "(no body)")
    out["priority"] = out["priority"].fillna("P2").astype(str).str.strip()
    out["intent"] = out["intent"].astype(str).str.strip()
    out["needs_reply"] = out["intent"].map(NEEDS_REPLY).fillna(out["needs_reply"].astype(str).str.strip())
    out["combined_text"] = (out["subject"] + " " + out["body"]).str.replace(r"\\s+", " ", regex=True).str.strip()
    out["word_count"] = out["combined_text"].str.findall(r"\\b\\w+\\b").str.len()
    out["subject_length"] = out["subject"].str.len()
    out["body_length"] = out["body"].str.len()
    out["contains_deadline"] = out["combined_text"].str.contains(DEADLINE_RE, regex=True)
    out["contains_money"] = out["combined_text"].str.contains(MONEY_RE, regex=True)
    out["contains_question"] = out["combined_text"].str.contains(QUESTION_RE, regex=True)
    out = out[out["word_count"] >= 5].copy()
    cols = ["subject","body","priority","intent","needs_reply","combined_text","word_count","subject_length","body_length","contains_deadline","contains_money","contains_question"]
    return out[cols].reset_index(drop=True)

def conflicting_body_count(df):
    count = 0
    for _, group in df.groupby("body", dropna=False):
        if len(group) <= 1:
            continue
        if len(group[["priority", "intent", "needs_reply"]].drop_duplicates()) > 1:
            count += 1
    return count
"""
    )
    md("## 3. Load Data")
    code(
        """
triage = pd.read_csv(SOURCE)
print("shape:", triage.shape)
print("columns:", triage.columns.tolist())
print("null counts:")
print(triage.isna().sum())
print("duplicate counts:")
print("exact duplicates:", triage.duplicated().sum())
print("duplicate bodies:", int(triage.duplicated(subset=["body"]).sum()))
triage.head()
"""
    )
    md("## 4. Resolve Conflicting Body Duplicates")
    code(
        """
def resolve_body_duplicates(df):
    retained = []
    rows_removed = 0
    rows_retained = 0

    for _, group in df.groupby("body", sort=False, dropna=False):
        group = group.copy()
        if len(group) == 1:
            retained.append(group.iloc[[0]])
            rows_retained += 1
            continue

        labels = list(group[["priority", "intent", "needs_reply"]].itertuples(index=False, name=None))
        combo_counts = Counter(labels)

        if len(combo_counts) > 1:
            majority_count = max(combo_counts.values())
            majority = next(label for label in labels if combo_counts[label] == majority_count)
            winner = group[
                (group["priority"] == majority[0])
                & (group["intent"] == majority[1])
                & (group["needs_reply"] == majority[2])
            ].iloc[[0]]
            retained.append(winner)
            rows_retained += 1
            rows_removed += len(group) - 1
        else:
            keep_n = min(2, len(group))
            kept = group.iloc[:keep_n]
            retained.append(kept)
            rows_retained += len(kept)
            rows_removed += len(group) - keep_n

    cleaned = pd.concat(retained, ignore_index=True)
    return cleaned, rows_removed, rows_retained

deduped, rows_removed, rows_retained = resolve_body_duplicates(triage)
print("rows removed:", rows_removed)
print("rows retained:", rows_retained)
deduped.head()
"""
    )
    md("## 5. Add Low-Urgency Reply-Needed Rows")
    code(
        """
def synth_row(intent, idx, rng):
    name = rng.choice(FIRST_NAMES)
    company = rng.choice(COMPANIES)
    topic = rng.choice(TOPICS)
    issue = rng.choice(ISSUES)
    time_phrase = rng.choice(TIMES)

    templates = {
        "Follow Up": (
            ["gentle follow up on previous note", "checking in when you have a moment", "quick follow up on the open item", "light follow up on our last message"],
            [
                f"Hi {name}, just checking if you had a chance to review {topic}. Please reply when convenient.",
                f"Hello {name}, following up on {topic}. There is no rush, but a short update would be helpful when you have time.",
                f"Hi {name}, I wanted to gently follow up on {topic}. Let me know when convenient if there is any progress to share.",
            ],
        ),
        "Meeting Request": (
            ["optional meeting next week", "open to a short meeting if useful", "would a light check-in be helpful?", "meeting request for a convenient time"],
            [
                f"Hello {name}, if helpful, we could schedule a short meeting {time_phrase} to review {topic}. Please let me know what works for you.",
                f"Hi {name}, there is no urgency, but I would be glad to meet {time_phrase} if you would like to discuss {topic}.",
                f"Hello {name}, let me know if you would still like to meet {time_phrase}. I am happy to work around your schedule.",
            ],
        ),
        "Complaint": (
            ["minor issue with invoice formatting", "small concern on the latest document", "light complaint about a recent detail", "small issue for review when convenient"],
            [
                f"Hello team, there is {issue}. It is not urgent, but please review it when convenient and let me know if a correction will be made.",
                f"Hi support, I noticed {issue} in the latest file from {company}. Please take a look when you have time.",
                f"Hello, I wanted to flag {issue}. The issue is minor, but I would appreciate a quick confirmation after your review.",
            ],
        ),
        "Quote Request": (
            ["quote clarification request", "small pricing question on the proposal", "quick clarification on one line item", "proposal detail to confirm"],
            [
                f"Hi {name}, could you clarify one line item in the proposal for {company} when you have time? I just want to confirm the pricing detail.",
                f"Hello {name}, I have a small question about the quote attached to {topic}. Please clarify the line item when convenient.",
                f"Hi {name}, when you have a moment, could you confirm one pricing detail in the latest quote? That will help us close out the review.",
            ],
        ),
        "Support Request": (
            ["small support question when convenient", "minor issue for the support team", "quick help request on a low-priority item", "support follow-up for a small issue"],
            [
                f"Hello support, I noticed {issue} in the {company} workflow. There is no urgency, but please review it when convenient.",
                f"Hi team, I have a small support request related to {topic}. Please take a look when you have time and let me know the best fix.",
                f"Hello support, there is a low-priority issue with the current setup. A response when convenient would be appreciated.",
            ],
        ),
    }

    subjects, bodies = templates[intent]
    return {
        "subject": rng.choice(subjects),
        "body": rng.choice(bodies),
        "priority": "P3",
        "intent": intent,
        "needs_reply": "Yes",
    }

def build_synthetic_p3_yes(existing, n_rows=150):
    rng = random.Random(SEED)
    rows = []
    seen = set(zip(existing["subject"], existing["body"], existing["intent"], existing["priority"], existing["needs_reply"]))
    counts = {intent: 0 for intent in P3_YES_INTENTS}
    per_intent = n_rows // len(P3_YES_INTENTS)
    targets = {intent: per_intent for intent in P3_YES_INTENTS}

    for intent in P3_YES_INTENTS:
        idx = 0
        while counts[intent] < targets[intent]:
            row = synth_row(intent, idx, rng)
            key = (clean_text(row["subject"]), clean_text(row["body"]), row["intent"], row["priority"], row["needs_reply"])
            idx += 1
            if key in seen:
                continue
            row["subject"] = clean_text(row["subject"])
            row["body"] = clean_text(row["body"])
            rows.append(row)
            seen.add(key)
            counts[intent] += 1
    return pd.DataFrame(rows)

synthetic_p3_yes = build_synthetic_p3_yes(deduped, n_rows=150)
synthetic_p3_yes.head()
"""
    )
    md("## 6. Top Up Low-Volume Intents")
    code(
        """
def synth_balance_row(intent, idx, rng):
    name = rng.choice(FIRST_NAMES)
    company = rng.choice(COMPANIES)
    topic = rng.choice(TOPICS)
    issue = rng.choice(ISSUES)
    time_phrase = rng.choice(TIMES)

    templates = {
        "Newsletter": (
            ["monthly product roundup", "customer newsletter for this month", "community update from the team", "newsletter: practical workflow ideas"],
            [
                f"Hello readers, this month's newsletter includes practical ideas for teams at {company}, a few customer highlights, and a short update on {topic}.",
                f"Hi there, here is our latest newsletter with customer stories, workflow notes, and a quick team update for the month.",
                f"Hello everyone, this edition covers helpful updates, a few launch notes, and practical guidance related to {topic}.",
            ],
            "P3",
            "No",
        ),
        "Internal FYI": (
            ["fyi for the internal team", "quick internal note", "visibility update for the team", "internal update for planning"],
            [
                f"Hello team, sharing this for visibility only. The latest note is about {topic}, and no action is needed right now.",
                f"Hi all, quick internal FYI that the team at {company} has updated the plan around {topic}.",
                f"Hello everyone, this is a simple internal note so the group has context before the next review.",
            ],
            "P3",
            "No",
        ),
        "Product Update": (
            ["product update for this week", "release note summary", "platform update from the team", "latest product improvements"],
            [
                f"Hello {name}, we released a product update related to {topic}. No action is required, but we wanted to share the latest improvements.",
                f"Hi team, this update includes a few product improvements and reliability fixes for teams using the platform at {company}.",
                f"Hello, sharing a quick product update with a few workflow improvements and minor fixes from this week's release.",
            ],
            "P3",
            "No",
        ),
        "Quote Request": (
            ["request for a refreshed quote", "pricing follow-up for review", "quote detail request", "budget quote request"],
            [
                f"Hi {name}, please send an updated quote for {company} when convenient so we can complete the review.",
                f"Hello {name}, we would appreciate a pricing quote tied to {topic}. Please send it over when you have time.",
                f"Hi team, we are looking for a quote with a little more detail on the proposed scope and pricing.",
            ],
            "P2",
            "Yes",
        ),
        "Follow Up": (
            ["follow up on the previous message", "checking in on an open item", "small follow-up request", "quick status follow-up"],
            [
                f"Hi {name}, I wanted to follow up on {topic}. Please send a short update when convenient.",
                f"Hello {name}, checking in on the open item from our last note. A quick reply would be appreciated.",
                f"Hi team, just following up to see whether there is any progress to share on {topic}.",
            ],
            "P2",
            "Yes",
        ),
        "Meeting Request": (
            ["schedule a short meeting", "meeting request for next week", "time to review the open item", "short discussion request"],
            [
                f"Hello {name}, would you be open to a short meeting {time_phrase} to discuss {topic}?",
                f"Hi {name}, please let me know if a brief meeting {time_phrase} would be useful for the next step.",
                f"Hello team, I would like to schedule a short meeting to review the open points around {topic}.",
            ],
            "P2",
            "Yes",
        ),
        "Complaint": (
            ["service issue for review", "customer concern about a recent issue", "problem reported by the team", "small complaint to review"],
            [
                f"Hello, I want to report {issue}. Please review it and let us know what correction you recommend.",
                f"Hi support, the team noticed {issue} and would appreciate a response on the next step.",
                f"Hello team, this issue is affecting our workflow and we would like someone to review it soon.",
            ],
            "P1",
            "Yes",
        ),
        "Support Request": (
            ["support request for review", "help needed on an open issue", "technical question from the team", "support follow-up request"],
            [
                f"Hello support, we need help reviewing {issue}. Please let us know the best next step.",
                f"Hi team, could someone take a look at {topic} and suggest the most practical fix?",
                f"Hello support, there is an open issue in the workflow and a short response would help the team move forward.",
            ],
            "P2",
            "Yes",
        ),
        "Sales Outreach": (
            ["idea to improve a workflow", "short intro if helpful", "supporting teams like yours", "note on process improvement"],
            [
                f"Hello {name}, we help teams like {company} simplify busy workflows and improve visibility. Let me know if a short intro would be useful.",
                f"Hi {name}, I thought our approach to workflow automation might be relevant to your team. I would be happy to share a quick overview.",
                f"Hello, reaching out because we support teams that want a more organized way to manage incoming work and follow-ups.",
            ],
            "P2",
            "Yes",
        ),
        "Investor Interest": (
            ["investor introduction note", "interest in learning more", "open to a brief conversation", "follow-up on company progress"],
            [
                f"Hello {name}, I have been following {company} and would be glad to schedule a short introductory conversation when convenient.",
                f"Hi {name}, I would welcome a chance to learn more about your progress and current priorities.",
                f"Hello, if helpful, I would be glad to connect and hear more about the team's direction over the coming months.",
            ],
            "P2",
            "Yes",
        ),
        "Interview Request": (
            ["interview scheduling request", "availability for an interview", "next interview step", "time to meet with the hiring team"],
            [
                f"Hello {name}, we would like to schedule an interview and would appreciate your availability for {time_phrase}.",
                f"Hi {name}, please let us know if you are open to a short interview conversation next week.",
                f"Hello, the hiring team would like to set up the next discussion when convenient for you.",
            ],
            "P2",
            "Yes",
        ),
        "Payment Reminder": (
            ["friendly payment reminder", "invoice still open", "reminder on the outstanding balance", "payment follow-up note"],
            [
                f"Hello {name}, this is a reminder that the invoice for {company} is still open. Please confirm the expected payment timing.",
                f"Hi {name}, we are following up on an outstanding balance and would appreciate a quick update.",
                f"Hello, please let us know if payment is already in process or if any clarification is needed from our side.",
            ],
            "P1",
            "Yes",
        ),
    }

    subjects, bodies, priority, needs_reply = templates[intent]
    return {"subject": rng.choice(subjects), "body": rng.choice(bodies), "priority": priority, "intent": intent, "needs_reply": needs_reply}

def top_up_low_intents(existing, min_rows=MIN_INTENT_ROWS):
    rng = random.Random(SEED + 7)
    rows = []
    seen = set(zip(existing["subject"], existing["body"], existing["intent"], existing["priority"], existing["needs_reply"]))
    counts = existing["intent"].value_counts().to_dict()

    for intent, current in counts.items():
        target = max(current, min_rows)
        idx = 0
        while counts.get(intent, 0) < target:
            row = synth_balance_row(intent, idx, rng)
            key = (clean_text(row["subject"]), clean_text(row["body"]), row["intent"], row["priority"], row["needs_reply"])
            idx += 1
            if key in seen:
                continue
            row["subject"] = clean_text(row["subject"])
            row["body"] = clean_text(row["body"])
            rows.append(row)
            seen.add(key)
            counts[intent] = counts.get(intent, 0) + 1
    return pd.DataFrame(rows)

top_up_rows = top_up_low_intents(pd.concat([deduped.drop(columns=["num_exclamations"], errors="ignore"), synthetic_p3_yes], ignore_index=True))
print("top-up rows added:", len(top_up_rows))
top_up_rows.head()
"""
    )
    md("## 7. Recalculate Features and Save Outputs")
    code(
        """
final_df = pd.concat([deduped.drop(columns=["num_exclamations"], errors="ignore"), synthetic_p3_yes, top_up_rows], ignore_index=True)
final_df = recalc_features(final_df)
final_df = final_df.drop_duplicates().reset_index(drop=True)

shutil.copy2(SOURCE, BACKUP)
final_df.to_csv(OUTPUT, index=False)

print("saved backup:", BACKUP.name)
print("saved final dataset:", OUTPUT.name)
final_df.head()
"""
    )
    md("## 8. Final Quality Checks")
    code(
        """
print("final shape:", final_df.shape)
print("\\nnull counts:")
print(final_df.isna().sum())
print("\\nduplicate exact rows:", final_df.duplicated().sum())
print("\\nduplicate bodies remaining:", int(final_df.duplicated(subset=["body"]).sum()))
print("\\nconflicting duplicate bodies remaining:", conflicting_body_count(final_df))
print("\\npriority distribution:")
print(final_df["priority"].value_counts().sort_index())
print("\\nintent distribution:")
print(final_df["intent"].value_counts().sort_index())
print("\\nneeds_reply distribution:")
print(final_df["needs_reply"].value_counts().sort_index())
print("\\nsample rows:")
final_df.head(10)
"""
    )
    md("## 9. Visualizations")
    code(
        """
fig, axes = plt.subplots(2, 2, figsize=(16, 12))

sns.countplot(data=final_df, x="priority", order=["P1", "P2", "P3"], ax=axes[0, 0], palette="crest")
axes[0, 0].set_title("Priority Distribution")
axes[0, 0].set_xlabel("Priority")

sns.countplot(data=final_df, y="intent", order=final_df["intent"].value_counts().index, ax=axes[0, 1], palette="flare")
axes[0, 1].set_title("Intent Distribution")
axes[0, 1].set_xlabel("Rows")
axes[0, 1].set_ylabel("")

sns.countplot(data=final_df, x="needs_reply", order=["Yes", "No"], ax=axes[1, 0], palette="mako")
axes[1, 0].set_title("Needs Reply Distribution")
axes[1, 0].set_xlabel("Needs Reply")

sns.histplot(data=final_df, x="word_count", bins=30, ax=axes[1, 1], color="#2A9D8F")
axes[1, 1].set_title("Word Count Histogram")
axes[1, 1].set_xlabel("Word Count")

plt.tight_layout()
plt.show()
"""
    )
    md("## 10. Final Summary")
    code(
        """
print("REPLYNT triage dataset finalized successfully.")
print(f"Rows: {len(final_df)}")
print(f"Intents: {final_df['intent'].nunique()}")
print("Ready for model training: YES")
print("Frozen version: triage_train_final.csv")
"""
    )

    notebook = {
        "cells": cells,
        "metadata": {
            "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
            "language_info": {"name": "python", "version": "3.13"},
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }
    NOTEBOOK.write_text(json.dumps(notebook, indent=2), encoding="utf-8")


def main() -> None:
    triage = pd.read_csv(SOURCE)
    inspect_dataset(triage, "loaded dataset")

    deduped, rows_removed, rows_retained = resolve_body_duplicates(triage)
    print("\nrows removed:", rows_removed)
    print("rows retained:", rows_retained)

    deduped = deduped.drop(columns=["num_exclamations"], errors="ignore")
    synthetic_p3_yes = build_synthetic_p3_yes(deduped, n_rows=150)
    top_up_rows = top_up_low_intents(pd.concat([deduped, synthetic_p3_yes], ignore_index=True), min_rows=MIN_INTENT_ROWS)
    print("top-up rows added:", len(top_up_rows))

    final_df = pd.concat([deduped, synthetic_p3_yes, top_up_rows], ignore_index=True)
    final_df = recalc_features(final_df)
    final_df = final_df.drop_duplicates().reset_index(drop=True)

    shutil.copy2(SOURCE, BACKUP)
    final_df.to_csv(OUTPUT, index=False)

    print()
    print_final_quality(final_df)
    build_notebook()
    print("\nREPLYNT triage dataset finalized successfully.")
    print(f"Rows: {len(final_df)}")
    print(f"Intents: {final_df['intent'].nunique()}")
    print("Ready for model training: YES")
    print("Frozen version: triage_train_final.csv")


if __name__ == "__main__":
    main()
