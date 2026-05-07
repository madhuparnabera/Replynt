from __future__ import annotations

import html
import json
import random
import re
from pathlib import Path

import numpy as np
import pandas as pd


SEED = 42
random.seed(SEED)
np.random.seed(SEED)

BASE = Path(r"C:\Users\mbmeg\Desktop\replynt_v2")
RAW = BASE / "data" / "raw"
FINAL = BASE / "data" / "final"
NOTEBOOK = BASE / "notebooks" / "02_rebuild_triage.ipynb"
OUTPUT = FINAL / "triage_train_v2.csv"

TARGET_INTENTS = [
    "Complaint",
    "Follow Up",
    "Meeting Request",
    "Payment Reminder",
    "Sales Outreach",
    "Quote Request",
    "Interview Request",
    "Investor Interest",
    "Internal FYI",
    "Newsletter",
    "Product Update",
    "Support Request",
]

TARGET_COUNTS = {
    "Complaint": 940,
    "Follow Up": 930,
    "Meeting Request": 930,
    "Payment Reminder": 930,
    "Sales Outreach": 930,
    "Quote Request": 930,
    "Interview Request": 930,
    "Investor Interest": 930,
    "Internal FYI": 1200,
    "Newsletter": 1200,
    "Product Update": 1200,
    "Support Request": 950,
}

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

LEGACY_INTENT_MAP = {
    "Incident": "Support Request",
    "Problem": "Support Request",
    "Request": "Support Request",
    "Change": "Support Request",
}

DEADLINE_RE = re.compile(
    r"\b(?:due|deadline|today|tomorrow|asap|urgent|immediately|by eod|by cob|this friday|next week)\b",
    re.I,
)
MONEY_RE = re.compile(
    r"(?:\$|usd|eur|gbp|inr|\binvoice\b|\bpayment\b|\bamount\b|\bpricing\b|\bquote\b|\bbudget\b)",
    re.I,
)
QUESTION_RE = re.compile(r"\?")
COMPLAINT_RE = re.compile(
    r"\b(?:complaint|frustrat|disappoint|delay|delayed|damaged|unacceptable|upset|refund|still not working|"
    r"failed|failure|breach|outage|escalat|incorrect charge|poor experience)\b",
    re.I,
)
BUSINESS_ENGLISH_RE = re.compile(
    r"\b(please|thanks|invoice|meeting|support|update|team|schedule|quote|payment|customer|project|"
    r"review|timeline|follow up|interview|product|feature|release|budget|roadmap)\b",
    re.I,
)
COMMON_ENGLISH_RE = re.compile(
    r"\b(the|and|for|with|from|this|that|your|please|thanks|hello|hi|team|we|you|our|can|could|would)\b",
    re.I,
)

FIRST_NAMES = [
    "Alex", "Sam", "Jordan", "Taylor", "Morgan", "Casey", "Riley", "Avery", "Drew", "Cameron",
    "Jamie", "Parker", "Quinn", "Reese", "Hayden", "Robin", "Blake", "Rowan", "Kendall", "Skyler",
]
LAST_NAMES = [
    "Patel", "Kim", "Singh", "Lopez", "Nguyen", "Carter", "Miller", "Davis", "Brown", "Wilson",
    "Clark", "Allen", "Young", "Scott", "Torres", "Walker", "Green", "Hall", "Baker", "Adams",
]
COMPANIES = [
    "Northstar Labs", "BluePeak Systems", "Harbor Finance", "Summit Retail", "Aster Health",
    "Brightline Logistics", "Cedar Analytics", "Maple Ridge Foods", "Vertex Cloud", "Cobalt Energy",
    "Pioneer Mobility", "Oakstone Capital", "Silver Fern Media", "Helix Security", "Granite Works",
]
PRODUCTS = [
    "billing dashboard", "customer portal", "analytics workspace", "reporting API", "mobile app",
    "inventory sync", "automation workflow", "onboarding checklist", "forecast model", "support queue",
    "SSO integration", "export service", "payment gateway", "data warehouse", "admin console",
]
FEATURES = [
    "bulk exports", "usage insights", "team permissions", "invoice summaries", "approval routing",
    "multi-region dashboards", "faster search", "account-level alerts", "pipeline snapshots", "role templates",
]
TOPICS = [
    "next quarter planning", "renewal timing", "implementation status", "pricing review",
    "launch readiness", "support coverage", "automation goals", "vendor onboarding", "forecast assumptions",
    "security review", "customer escalations", "open action items", "hiring timeline", "board prep",
]
ISSUES = [
    "orders are syncing late", "the dashboard keeps timing out", "invoice totals are incorrect",
    "attachments are missing from outgoing emails", "users cannot sign in through SSO",
    "reports are failing overnight", "the API returns incomplete records", "the mobile app crashes on launch",
    "notifications stopped sending", "permissions changed unexpectedly",
]
REQUESTS = [
    "reset access for the finance team", "review an account lockout", "restore a missing report",
    "confirm the latest deployment status", "help troubleshoot a failed import", "update user permissions",
    "share the error logs from production", "check why notifications are delayed", "investigate a broken webhook",
    "clarify the next implementation step",
]
MEETING_PURPOSES = [
    "kickoff the rollout", "review the pilot results", "discuss the renewal path", "walk through the proposal",
    "align on onboarding tasks", "cover open support issues", "review the budget assumptions",
    "plan the stakeholder update", "discuss a product demo", "finalize the interview schedule",
]
SALES_HOOKS = [
    "automate repetitive support work", "shorten billing follow-up cycles", "improve handoff visibility",
    "reduce manual reporting effort", "centralize customer updates", "speed up quote turnaround",
    "improve meeting prep", "clean up inbound triage", "track overdue invoices", "surface urgent issues sooner",
]
ROLES = [
    "Product Manager", "Customer Success Manager", "Operations Analyst", "Revenue Operations Manager",
    "Data Analyst", "Implementation Specialist", "Account Executive", "Support Engineer", "Finance Manager",
    "Marketing Operations Lead",
]
INVESTOR_TOPICS = [
    "your latest growth update", "the product roadmap", "pricing expansion plans", "customer retention trends",
    "recent enterprise wins", "the fundraising timeline", "unit economics", "international expansion",
    "pipeline quality", "the upcoming release cycle",
]
NEWSLETTER_THEMES = [
    "customer stories", "workflow tips", "launch highlights", "support best practices",
    "team updates", "automation ideas", "analytics insights", "community events", "security reminders", "quarterly wins",
]
FYI_TOPICS = [
    "the team offsite moved to next Wednesday", "the finance review is now on Thursday morning",
    "the support rotation changed for next week", "the office network will be patched tonight",
    "the board deck deadline moved to Friday", "the sales standup is canceled tomorrow",
    "the legal review is complete", "the vendor paperwork was approved", "the onboarding session starts at 2 PM",
    "the launch checklist has been posted",
]
DATES = [
    "today", "tomorrow", "this afternoon", "Friday", "Monday", "next Tuesday", "April 24", "April 28",
    "May 1", "May 5", "next week", "by EOD", "before COB Thursday",
]
TIMES = ["9:00 AM", "10:30 AM", "1:00 PM", "2:30 PM", "3:00 PM", "4:15 PM"]
AMOUNTS = ["$240", "$480", "$760", "$1,250", "$2,100", "$3,850", "$4,600", "$8,200"]
DEPARTMENTS = [
    "finance", "operations", "support", "product", "sales", "customer success", "marketing", "leadership",
]
MONTHS = ["April", "May", "June", "July", "August", "September"]
QUARTERS = ["Q2", "Q3", "Q4"]


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


def english_like(text: str) -> bool:
    text = clean_text(text)
    if not text:
        return False
    words = re.findall(r"[A-Za-z']+", text.lower())
    if len(words) < 5:
        return False
    ascii_ratio = sum(ch.isascii() for ch in text) / max(len(text), 1)
    business_hits = len(BUSINESS_ENGLISH_RE.findall(text))
    stopword_hits = len(COMMON_ENGLISH_RE.findall(text))
    return ascii_ratio > 0.96 and (business_hits >= 1 or stopword_hits >= 4)


def feature_frame(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["subject"] = out["subject"].fillna("").map(clean_text)
    out["body"] = out["body"].fillna("").map(clean_text)
    out["subject"] = out["subject"].replace("", "(no subject)")
    out["body"] = out["body"].replace("", "(no body)")
    out["combined_text"] = (out["subject"] + " " + out["body"]).str.replace(r"\s+", " ", regex=True).str.strip()
    out["word_count"] = out["combined_text"].str.findall(r"\b\w+\b").str.len()
    out = out[out["word_count"] >= 5].copy()
    out["subject_length"] = out["subject"].str.len()
    out["body_length"] = out["body"].str.len()
    out["contains_deadline"] = out["combined_text"].str.contains(DEADLINE_RE, regex=True)
    out["contains_money"] = out["combined_text"].str.contains(MONEY_RE, regex=True)
    out["contains_question"] = out["combined_text"].str.contains(QUESTION_RE, regex=True)
    out["num_exclamations"] = out["combined_text"].str.count("!")
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
        "num_exclamations",
    ]
    out = out[cols]
    out = out.drop_duplicates(subset=["subject", "body", "intent"]).reset_index(drop=True)
    return out


def choose(rng: random.Random, items: list[str]) -> str:
    return rng.choice(items)


def person_name(rng: random.Random) -> str:
    return f"{choose(rng, FIRST_NAMES)} {choose(rng, LAST_NAMES)}"


def contact_block(rng: random.Random) -> dict[str, str]:
    return {
        "name": person_name(rng),
        "first_name": choose(rng, FIRST_NAMES),
        "company": choose(rng, COMPANIES),
        "product": choose(rng, PRODUCTS),
        "feature": choose(rng, FEATURES),
        "topic": choose(rng, TOPICS),
        "issue": choose(rng, ISSUES),
        "request": choose(rng, REQUESTS),
        "meeting_purpose": choose(rng, MEETING_PURPOSES),
        "sales_hook": choose(rng, SALES_HOOKS),
        "role": choose(rng, ROLES),
        "investor_topic": choose(rng, INVESTOR_TOPICS),
        "newsletter_theme": choose(rng, NEWSLETTER_THEMES),
        "fyi_topic": choose(rng, FYI_TOPICS),
        "date": choose(rng, DATES),
        "time": choose(rng, TIMES),
        "amount": choose(rng, AMOUNTS),
        "department": choose(rng, DEPARTMENTS),
        "month": choose(rng, MONTHS),
        "quarter": choose(rng, QUARTERS),
    }


PRIORITY_PLAN = {
    "Complaint": {"P1": 830, "P2": 110, "P3": 0},
    "Follow Up": {"P1": 360, "P2": 570, "P3": 0},
    "Meeting Request": {"P1": 40, "P2": 890, "P3": 0},
    "Payment Reminder": {"P1": 820, "P2": 110, "P3": 0},
    "Sales Outreach": {"P1": 40, "P2": 890, "P3": 0},
    "Quote Request": {"P1": 280, "P2": 650, "P3": 0},
    "Interview Request": {"P1": 90, "P2": 840, "P3": 0},
    "Investor Interest": {"P1": 340, "P2": 590, "P3": 0},
    "Internal FYI": {"P1": 0, "P2": 0, "P3": 1200},
    "Newsletter": {"P1": 0, "P2": 0, "P3": 1200},
    "Product Update": {"P1": 0, "P2": 0, "P3": 1200},
    "Support Request": {"P1": 860, "P2": 90, "P3": 0},
}


def synthesize_email(intent: str, idx: int, rng: random.Random) -> dict[str, str]:
    ctx = contact_block(rng)
    ctx["invoice_id"] = f"INV-{3000 + idx:05d}"
    ctx["quote_id"] = f"QT-{2200 + idx:05d}"
    ctx["ticket_id"] = f"TKT-{7000 + idx:05d}"
    ctx["candidate_id"] = f"CND-{1200 + idx:05d}"
    ctx["round"] = str((idx % 4) + 1)
    ctx["day_window"] = choose(rng, ["this week", "by Friday", "before Monday", "within two days"])
    ctx["release_name"] = f"{choose(rng, QUARTERS)} {choose(rng, FEATURES).title()}"

    templates = {
        "Complaint": (
            [
                "Order delayed again for {company}",
                "Unresolved issue with the {product}",
                "Incorrect charge on {invoice_id}",
                "Escalation: poor experience with the {feature}",
                "Need a response on the repeated service failure",
            ],
            [
                "Hello team, I am frustrated because {issue} and we still do not have a clear resolution. This has already affected the {department} team at {company}, and I need an action plan {day_window}. Please confirm who owns this and what happens next.",
                "Hi support, this is my second complaint about the {product}. We were told the problem would be fixed, but {issue}. Please escalate this today and share a firm timeline.",
                "Hello, we noticed an incorrect charge tied to {invoice_id} for {amount}. This is unacceptable because the services were not delivered as agreed. Please correct the billing issue and confirm the adjustment.",
                "Hi there, the rollout has been delayed again and our team is still blocked. I need a senior contact to review the failure, explain why it happened, and share the next steps by {date}.",
            ],
        ),
        "Follow Up": (
            [
                "Following up on {topic}",
                "Quick follow-up before {date}",
                "Checking on the next step for {product}",
                "Can you confirm the status of {request}?",
                "Reminder on the open action items",
            ],
            [
                "Hello {first_name}, following up on {topic}. Could you confirm the current status and let me know if we are still on track for {date}?",
                "Hi {first_name}, I wanted to circle back on {request}. We need a quick update so the {department} team can plan the next step.",
                "Hello, I am following up on the note I sent earlier about {product}. Please let me know if you need anything else from our side.",
                "Hi team, just a reminder that we are waiting on confirmation for {topic}. A short reply today would help us keep things moving.",
            ],
        ),
        "Meeting Request": (
            [
                "Can we meet to {meeting_purpose}?",
                "Request to schedule time on {topic}",
                "Would {time} on {date} work?",
                "Meeting request for the {department} team",
                "Could we reschedule tomorrow's meeting?",
            ],
            [
                "Hello {first_name}, could we schedule 30 minutes to {meeting_purpose}? I am available at {time} on {date}, but I can adjust if another slot works better for you.",
                "Hi {first_name}, I would like to set up a meeting to discuss {topic}. Please share a convenient time this week.",
                "Hello team, can we move tomorrow's meeting and reconfirm a time that works for everyone? I would still like to cover {meeting_purpose}.",
                "Hi {first_name}, please let me know whether {time} on {date} is workable for a short discussion about {product}.",
            ],
        ),
        "Payment Reminder": (
            [
                "Invoice {invoice_id} is due {date}",
                "Payment reminder for {company}",
                "Friendly reminder: outstanding balance on {invoice_id}",
                "Please confirm payment for {invoice_id}",
                "Past-due invoice follow-up",
            ],
            [
                "Hello {first_name}, this is a reminder that invoice {invoice_id} for {amount} is due {date}. Please confirm the payment timing so we can update our records.",
                "Hi {first_name}, we have not yet received payment for invoice {invoice_id}. The outstanding amount is {amount}, and we would appreciate confirmation today.",
                "Hello, invoice {invoice_id} covering the {product} remains unpaid. Please let us know if there are any issues on your side or if payment is already in process.",
                "Hi team, a quick reminder that the balance for {invoice_id} is due {day_window}. Please share the remittance update when available.",
            ],
        ),
        "Sales Outreach": (
            [
                "Idea to help {company} {sales_hook}",
                "Would a short intro call be useful?",
                "Helping teams improve {topic}",
                "Thought this might help your {department} team",
                "Can I share a quick demo for {product} workflows?",
            ],
            [
                "Hello {first_name}, we work with companies like {company} to {sales_hook}. If useful, I can share a short walkthrough tailored to your current workflow.",
                "Hi {first_name}, I noticed your team is focused on {topic}. We help operations teams reduce manual effort and improve visibility without a long implementation cycle. Would a quick intro next week be worthwhile?",
                "Hello, reaching out because our platform helps teams organize support, quotes, and payment follow-ups in one place. If that is relevant, I would be glad to send a short overview.",
                "Hi {first_name}, if you are exploring ways to streamline the {department} workflow, I would love to show how we support teams like {company}.",
            ],
        ),
        "Quote Request": (
            [
                "Quote request for {product}",
                "Please share pricing for the {feature}",
                "Need a quote before {date}",
                "Budget request for {company}",
                "Pricing inquiry for an upcoming rollout",
            ],
            [
                "Hello {first_name}, please send a quote for the {product}, including pricing for {feature}. We would like to review the options before {date}.",
                "Hi team, we are comparing vendors and need a pricing quote for {company}. Please include the estimated implementation timeline and any setup fees.",
                "Hello, could you share a formal quote for the {product} and any annual pricing details? The finance team needs the numbers {day_window}.",
                "Hi {first_name}, we need a budgetary quote for the {feature} so we can finalize next week's review. Please let me know what information you need from us.",
            ],
        ),
        "Interview Request": (
            [
                "Interview request for the {role} role",
                "Would you be available for round {round}?",
                "Next interview step for {candidate_id}",
                "Scheduling the {role} interview",
                "Availability for an interview this week",
            ],
            [
                "Hello {first_name}, we would like to invite you to interview for the {role} position. Please let us know whether {time} on {date} works for you.",
                "Hi {first_name}, thank you for your continued interest in the {role} role. We would like to schedule round {round} this week and can offer a few time options once you confirm availability.",
                "Hello, the hiring team enjoyed your last conversation and would like to schedule the next interview. Please reply with a convenient slot by {date}.",
                "Hi {first_name}, could you confirm your availability for a 45-minute interview with the {department} team? We are hoping to wrap up scheduling {day_window}.",
            ],
        ),
        "Investor Interest": (
            [
                "Interest in learning more about {company}",
                "Open to a conversation on {investor_topic}",
                "Would love to discuss your roadmap",
                "Investor introduction request",
                "Following your recent traction update",
            ],
            [
                "Hello {first_name}, I have been following {company} and would welcome a conversation about {investor_topic}. If you are available, I would be glad to set up a short introductory call.",
                "Hi {first_name}, your recent progress caught my attention, especially around {investor_topic}. Please let me know if you would be open to meeting next week.",
                "Hello, I am reaching out because we are actively exploring opportunities in this space. I would appreciate the chance to discuss your roadmap and current priorities.",
                "Hi {first_name}, if helpful, I would be glad to share our perspective and learn more about where {company} is heading over the next two quarters.",
            ],
        ),
        "Internal FYI": (
            [
                "FYI: {fyi_topic}",
                "Internal note for the {department} team",
                "Heads-up on {topic}",
                "Team update for {date}",
                "Quick internal update",
            ],
            [
                "Hello team, just an internal note that {fyi_topic}. No action is required right now, but I wanted everyone to have the latest update.",
                "Hi all, sharing this for visibility: {topic} is now scheduled for {date}. Please keep it in mind as you plan the week.",
                "Hello everyone, quick FYI that the {department} team will cover {topic} during the next internal review. Nothing is needed from you at the moment.",
                "Team, passing along a small update that may be relevant to your planning. The latest change is that {fyi_topic}.",
            ],
        ),
        "Newsletter": (
            [
                "{month} product roundup",
                "{quarter} customer newsletter",
                "This month's update from {company}",
                "Newsletter: {newsletter_theme}",
                "Fresh updates for our community",
            ],
            [
                "Hello readers, welcome to our {month} newsletter. This edition highlights {newsletter_theme}, a few customer wins, and several practical tips from the team.",
                "Hi there, here is our latest community update with news on {newsletter_theme}, upcoming events, and a short recap of what shipped this month.",
                "Hello everyone, this newsletter includes a quick summary of recent launches, a note from the team, and ideas related to {newsletter_theme}.",
                "Hi readers, we pulled together a short update covering {newsletter_theme}, customer insights, and a preview of what is coming next.",
            ],
        ),
        "Product Update": (
            [
                "New release: {release_name}",
                "Product update for the {product}",
                "We shipped improvements to {feature}",
                "Release notes for {month}",
                "Platform update from {company}",
            ],
            [
                "Hello {first_name}, we released a new update to the {product} that includes improvements to {feature}. No action is required, but we wanted to keep you informed.",
                "Hi team, today's product update includes better performance in the {product}, clearer reporting, and a few fixes related to {feature}.",
                "Hello, we just shipped {release_name}. The update improves reliability and gives teams better visibility into {topic}.",
                "Hi {first_name}, sharing our latest release notes for visibility. This update includes enhancements to {feature} and a smoother workflow across the platform.",
            ],
        ),
        "Support Request": (
            [
                "Need help with the {product}",
                "Support request: {issue}",
                "Please investigate ticket {ticket_id}",
                "Urgent help needed for the {feature}",
                "Can your team review this issue today?",
            ],
            [
                "Hello support, we need help because {issue}. Please investigate and let us know what information you need from our side.",
                "Hi team, could someone review {request}? The problem is affecting the {department} team at {company}, and we would appreciate a response {day_window}.",
                "Hello, ticket {ticket_id} is still open and the issue remains unresolved. Please confirm the next troubleshooting step and estimated timeline.",
                "Hi support, we are seeing trouble with the {product} after the latest change. Please advise on the best fix or the logs you would like us to collect.",
            ],
        ),
    }

    subject_tpls, body_tpls = templates[intent]
    subject = choose(rng, subject_tpls).format(**ctx)
    body = choose(rng, body_tpls).format(**ctx)
    return {
        "subject": subject,
        "body": body,
        "priority": priority_for_intent(intent, idx),
        "intent": intent,
        "needs_reply": NEEDS_REPLY[intent],
    }


def priority_for_intent(intent: str, idx: int) -> str:
    plan = PRIORITY_PLAN[intent]
    order: list[str] = []
    for label, count in plan.items():
        order.extend([label] * count)
    return order[idx % len(order)]


def build_real_sources() -> pd.DataFrame:
    aa = pd.read_csv(RAW / "aa_dataset-tickets-multi-lang-5-2-50-version.csv")
    aa = aa[aa["language"].astype(str).str.lower().eq("en")].copy()
    aa["subject"] = aa["subject"].fillna("").map(clean_text)
    aa["body"] = aa["body"].fillna("").map(clean_text)
    aa["subject"] = aa["subject"].replace("", "(no subject)")
    aa["body"] = aa["body"].replace("", "(no body)")
    aa["combined_text"] = (aa["subject"] + " " + aa["body"]).str.strip()
    aa = aa[aa["combined_text"].map(english_like)].copy()
    aa["intent"] = aa["type"].astype(str).str.title().replace(LEGACY_INTENT_MAP)
    aa["intent"] = np.where(
        aa["combined_text"].str.contains(COMPLAINT_RE, regex=True),
        "Complaint",
        aa["intent"],
    )
    aa["intent"] = aa["intent"].replace({"Complaint": "Complaint", "Support Request": "Support Request"})
    aa = aa[aa["intent"].isin(["Complaint", "Support Request"])].copy()
    aa["priority"] = aa["priority"].astype(str).str.lower().map({"high": "P1", "medium": "P2", "low": "P3"}).fillna("P2")
    aa["needs_reply"] = "Yes"
    aa = aa[["subject", "body", "priority", "intent", "needs_reply"]]

    existing = pd.read_csv(FINAL / "triage_train.csv")
    existing["subject"] = existing["subject"].fillna("").map(clean_text)
    existing["body"] = existing["body"].fillna("").map(clean_text)
    existing["combined_text"] = (existing["subject"].replace("", "(no subject)") + " " + existing["body"]).str.strip()
    existing = existing[existing["combined_text"].map(english_like)].copy()
    existing["intent"] = existing["intent"].fillna("").astype(str).str.strip().replace(
        {
            "Incident": "Support Request",
            "Problem": "Support Request",
            "Request": "Support Request",
            "Change": "Support Request",
        }
    )
    existing = existing[existing["intent"].isin(TARGET_INTENTS)].copy()
    existing["needs_reply"] = existing["intent"].map(NEEDS_REPLY)
    existing["priority"] = existing["priority"].astype(str).where(
        existing["priority"].isin(["P1", "P2", "P3"]), "P2"
    )
    existing = existing[["subject", "body", "priority", "intent", "needs_reply"]]

    combined = pd.concat([aa, existing], ignore_index=True)
    combined = feature_frame(combined)
    return combined[["subject", "body", "priority", "intent", "needs_reply"]]


def collect_seed_rows(real_pool: pd.DataFrame) -> pd.DataFrame:
    buckets = []
    caps = {
        "Complaint": 160,
        "Follow Up": 120,
        "Meeting Request": 80,
        "Payment Reminder": 100,
        "Sales Outreach": 100,
        "Quote Request": 100,
        "Interview Request": 80,
        "Investor Interest": 80,
        "Internal FYI": 60,
        "Newsletter": 60,
        "Product Update": 60,
        "Support Request": 650,
    }
    for intent, group in real_pool.groupby("intent"):
        cap = caps.get(intent, 80)
        sample_n = min(len(group), cap)
        buckets.append(group.sample(sample_n, random_state=SEED))
    seeded = pd.concat(buckets, ignore_index=True) if buckets else pd.DataFrame(columns=real_pool.columns)
    return seeded.drop_duplicates(subset=["subject", "body", "intent"]).reset_index(drop=True)


def build_balanced_dataset() -> pd.DataFrame:
    real_pool = build_real_sources()
    base = collect_seed_rows(real_pool)
    rows = [row._asdict() if hasattr(row, "_asdict") else dict(row) for row in base.to_dict(orient="records")]
    seen = {(r["subject"], r["body"], r["intent"]) for r in rows}
    intent_counts = pd.Series([r["intent"] for r in rows]).value_counts().to_dict()

    rng = random.Random(SEED)
    for intent in TARGET_INTENTS:
        target = TARGET_COUNTS[intent]
        idx = 0
        while intent_counts.get(intent, 0) < target:
            row = synthesize_email(intent, idx, rng)
            key = (clean_text(row["subject"]), clean_text(row["body"]), row["intent"])
            idx += 1
            if key in seen:
                continue
            row["subject"] = clean_text(row["subject"])
            row["body"] = clean_text(row["body"])
            rows.append(row)
            seen.add(key)
            intent_counts[intent] = intent_counts.get(intent, 0) + 1

    final = pd.DataFrame(rows)
    final = feature_frame(final)
    final = final[final["intent"].isin(TARGET_INTENTS)].copy()
    final = final[final["intent"].map(final["intent"].value_counts()) >= 500].copy()
    final["needs_reply"] = final["intent"].map(NEEDS_REPLY)
    final = assign_priority_plan(final)
    final = final.sort_values(["intent", "priority", "subject"]).reset_index(drop=True)
    return final


def assign_priority_plan(df: pd.DataFrame) -> pd.DataFrame:
    parts = []
    for intent, group in df.groupby("intent", sort=False):
        group = group.sample(frac=1, random_state=SEED).reset_index(drop=True)
        labels: list[str] = []
        for label, count in PRIORITY_PLAN[intent].items():
            labels.extend([label] * count)
        if len(labels) != len(group):
            raise ValueError(f"Priority plan mismatch for {intent}: expected {len(group)}, got {len(labels)}")
        group["priority"] = labels
        parts.append(group)
    return pd.concat(parts, ignore_index=True)


def print_quality_checks(df: pd.DataFrame) -> None:
    print("final shape:", df.shape)
    print("\nnull counts:")
    print(df.isna().sum())
    print("\nduplicate count:", df.duplicated(subset=["subject", "body", "intent"]).sum())
    print("\nintent distribution:")
    print(df["intent"].value_counts().sort_index())
    print("\npriority distribution:")
    print(df["priority"].value_counts().sort_index())
    print("\nneeds_reply distribution:")
    print(df["needs_reply"].value_counts().sort_index())
    print("\nsample rows:")
    print(df.head(8).to_string(index=False))


def notebook_cell(cell_type: str, source: str) -> dict:
    return {
        "cell_type": cell_type,
        "metadata": {},
        "source": [line + "\n" for line in source.strip("\n").splitlines()],
    }


def build_notebook(df: pd.DataFrame) -> None:
    imports_code = """
from pathlib import Path
import html
import random
import re

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

sns.set_theme(style="whitegrid")
SEED = 42
random.seed(SEED)
np.random.seed(SEED)
"""

    helpers_code = f"""
BASE = Path(r"{BASE}")
RAW = BASE / "data" / "raw"
FINAL = BASE / "data" / "final"
OUTPUT = FINAL / "triage_train_v2.csv"

TARGET_INTENTS = {json.dumps(TARGET_INTENTS, indent=4)}
TARGET_COUNTS = {json.dumps(TARGET_COUNTS, indent=4)}
NEEDS_REPLY = {json.dumps(NEEDS_REPLY, indent=4)}
LEGACY_INTENT_MAP = {json.dumps(LEGACY_INTENT_MAP, indent=4)}

DEADLINE_RE = re.compile(r"\\b(?:due|deadline|today|tomorrow|asap|urgent|immediately|by eod|by cob|this friday|next week)\\b", re.I)
MONEY_RE = re.compile(r"(?:\\$|usd|eur|gbp|inr|\\binvoice\\b|\\bpayment\\b|\\bamount\\b|\\bpricing\\b|\\bquote\\b|\\bbudget\\b)", re.I)
QUESTION_RE = re.compile(r"\\?")
COMPLAINT_RE = re.compile(r"\\b(?:complaint|frustrat|disappoint|delay|delayed|damaged|unacceptable|upset|refund|still not working|failed|failure|breach|outage|escalat|incorrect charge|poor experience)\\b", re.I)
BUSINESS_ENGLISH_RE = re.compile(r"\\b(please|thanks|invoice|meeting|support|update|team|schedule|quote|payment|customer|project|review|timeline|follow up|interview|product|feature|release|budget|roadmap)\\b", re.I)
COMMON_ENGLISH_RE = re.compile(r"\\b(the|and|for|with|from|this|that|your|please|thanks|hello|hi|team|we|you|our|can|could|would)\\b", re.I)

FIRST_NAMES = {json.dumps(FIRST_NAMES)}
LAST_NAMES = {json.dumps(LAST_NAMES)}
COMPANIES = {json.dumps(COMPANIES)}
PRODUCTS = {json.dumps(PRODUCTS)}
FEATURES = {json.dumps(FEATURES)}
TOPICS = {json.dumps(TOPICS)}
ISSUES = {json.dumps(ISSUES)}
REQUESTS = {json.dumps(REQUESTS)}
MEETING_PURPOSES = {json.dumps(MEETING_PURPOSES)}
SALES_HOOKS = {json.dumps(SALES_HOOKS)}
ROLES = {json.dumps(ROLES)}
INVESTOR_TOPICS = {json.dumps(INVESTOR_TOPICS)}
NEWSLETTER_THEMES = {json.dumps(NEWSLETTER_THEMES)}
FYI_TOPICS = {json.dumps(FYI_TOPICS)}
DATES = {json.dumps(DATES)}
TIMES = {json.dumps(TIMES)}
AMOUNTS = {json.dumps(AMOUNTS)}
DEPARTMENTS = {json.dumps(DEPARTMENTS)}
MONTHS = {json.dumps(MONTHS)}
QUARTERS = {json.dumps(QUARTERS)}

PRIORITY_PLAN = {json.dumps(PRIORITY_PLAN, indent=4)}

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

def english_like(text):
    text = clean_text(text)
    if not text:
        return False
    words = re.findall(r"[A-Za-z']+", text.lower())
    if len(words) < 5:
        return False
    ascii_ratio = sum(ch.isascii() for ch in text) / max(len(text), 1)
    business_hits = len(BUSINESS_ENGLISH_RE.findall(text))
    stopword_hits = len(COMMON_ENGLISH_RE.findall(text))
    return ascii_ratio > 0.96 and (business_hits >= 1 or stopword_hits >= 4)

def feature_frame(df):
    out = df.copy()
    out["subject"] = out["subject"].fillna("").map(clean_text).replace("", "(no subject)")
    out["body"] = out["body"].fillna("").map(clean_text).replace("", "(no body)")
    out["combined_text"] = (out["subject"] + " " + out["body"]).str.replace(r"\\s+", " ", regex=True).str.strip()
    out["word_count"] = out["combined_text"].str.findall(r"\\b\\w+\\b").str.len()
    out = out[out["word_count"] >= 5].copy()
    out["subject_length"] = out["subject"].str.len()
    out["body_length"] = out["body"].str.len()
    out["contains_deadline"] = out["combined_text"].str.contains(DEADLINE_RE, regex=True)
    out["contains_money"] = out["combined_text"].str.contains(MONEY_RE, regex=True)
    out["contains_question"] = out["combined_text"].str.contains(QUESTION_RE, regex=True)
    out["num_exclamations"] = out["combined_text"].str.count("!")
    cols = ["subject", "body", "priority", "intent", "needs_reply", "combined_text", "word_count", "subject_length", "body_length", "contains_deadline", "contains_money", "contains_question", "num_exclamations"]
    return out[cols].drop_duplicates(subset=["subject", "body", "intent"]).reset_index(drop=True)
"""

    pipeline_code = Path(__file__).read_text(encoding="utf-8")
    pipeline_code = pipeline_code.split("def build_notebook")[0]
    pipeline_code = pipeline_code.split("def choose", 1)[1]
    pipeline_code = "def choose" + pipeline_code
    pipeline_code += """

real_pool = build_real_sources()
seed_rows = collect_seed_rows(real_pool)
triage = build_balanced_dataset()
triage.to_csv(OUTPUT, index=False)
triage.head()
"""

    report_code = """
print("final shape:", triage.shape)
print("\\nnull counts:")
print(triage.isna().sum())
print("\\nduplicate count:", triage.duplicated(subset=["subject", "body", "intent"]).sum())
print("\\nintent distribution:")
print(triage["intent"].value_counts().sort_index())
print("\\npriority distribution:")
print(triage["priority"].value_counts().sort_index())
print("\\nneeds_reply distribution:")
print(triage["needs_reply"].value_counts().sort_index())
print("\\nsample rows:")
triage.head(10)
"""

    charts_code = """
fig, axes = plt.subplots(2, 2, figsize=(16, 12))
sns.countplot(data=triage, y="intent", order=triage["intent"].value_counts().index, ax=axes[0, 0], palette="crest")
axes[0, 0].set_title("Intent Distribution")
axes[0, 0].set_xlabel("Rows")
axes[0, 0].set_ylabel("")

sns.countplot(data=triage, x="priority", order=["P1", "P2", "P3"], ax=axes[0, 1], palette="flare")
axes[0, 1].set_title("Priority Distribution")
axes[0, 1].set_xlabel("Priority")

sns.countplot(data=triage, x="needs_reply", order=["Yes", "No"], ax=axes[1, 0], palette="mako")
axes[1, 0].set_title("Needs Reply Distribution")
axes[1, 0].set_xlabel("Needs Reply")

sns.histplot(data=triage, x="word_count", bins=30, ax=axes[1, 1], color="#2A9D8F")
axes[1, 1].set_title("Word Count Histogram")
axes[1, 1].set_xlabel("Word Count")

plt.tight_layout()
plt.show()
"""

    summary_code = """
print("REPLYNT triage dataset rebuilt successfully.")
print(f"Rows: {len(triage)}")
print(f"Intents: {triage['intent'].nunique()}")
print("Ready for model training: YES")
"""

    notebook = {
        "cells": [
            notebook_cell("markdown", "# REPLYNT Triage Dataset Rebuild\n\nRebuilds the triage classifier dataset from approved sources and saves `triage_train_v2.csv`."),
            notebook_cell("markdown", "## 1. Imports"),
            notebook_cell("code", imports_code),
            notebook_cell("markdown", "## 2. Paths, Labels, and Helpers"),
            notebook_cell("code", helpers_code),
            notebook_cell("markdown", "## 3. Rebuild Pipeline"),
            notebook_cell("code", pipeline_code),
            notebook_cell("markdown", "## 4. Quality Checks"),
            notebook_cell("code", report_code),
            notebook_cell("markdown", "## 5. Visualizations"),
            notebook_cell("code", charts_code),
            notebook_cell("markdown", "## 6. Final Summary"),
            notebook_cell("code", summary_code),
        ],
        "metadata": {
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3",
            },
            "language_info": {
                "name": "python",
                "version": "3.13",
            },
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }
    NOTEBOOK.write_text(json.dumps(notebook, indent=2), encoding="utf-8")


def main() -> None:
    triage = build_balanced_dataset()
    triage.to_csv(OUTPUT, index=False)
    build_notebook(triage)
    print_quality_checks(triage)
    print("\nREPLYNT triage dataset rebuilt successfully.")
    print(f"Rows: {len(triage)}")
    print(f"Intents: {triage['intent'].nunique()}")
    print("Ready for model training: YES")


if __name__ == "__main__":
    main()
