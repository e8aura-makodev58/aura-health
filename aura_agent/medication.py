"""Curated medication information. The model may only choose a topic; it never writes answers."""

import json
import re
from pathlib import Path

INFO = json.loads(Path(__file__).with_name("medication_info.json").read_text())
TOPIC_IDS = tuple(topic["id"] for topic in INFO["topics"])
ABSTAIN_MEDICATION = INFO["abstain_unknown_medication"]
ABSTAIN_TOPIC = INFO["abstain_unknown_topic"]
ADVICE_REQUEST = INFO["advice_request"]
# Requests to change treatment are never answered from leaflet text.
CHANGE_WORDS = ("increase", "decrease", "reduce", "lower", "raise", "stop", "stopping", "quit", "double",
                "halve", "switch", "change", "taper", "come off", "more", "less", "extra", "skip it")

# Ordered: the first matching topic wins. Whole words only.
KEYWORDS = (
    ("missed_dose", ("miss", "missed", "forgot", "forget", "skipped", "skip")),
    ("side_effects", ("side effect", "side effects", "nausea", "sick", "headache", "sleepy", "insomnia")),
    ("alcohol", ("alcohol", "drink", "drinking", "beer", "wine")),
    ("how_to_take", ("how do i take", "how to take", "when do i take", "when should i take", "with food",
                     "what time", "morning", "dose", "how much")),
    ("purpose", ("what is it for", "what's it for", "what is this for", "why do i take", "what does it do",
                 "what is sertraline", "what is escitalopram", "what is fluoxetine", "purpose")),
)
OTHER_MEDICATION_WORDS = ("ibuprofen", "paracetamol", "panadol", "aspirin", "melatonin", "antibiotic",
                          "lithium", "diazepam", "codeine", "st john", "supplement", "vitamin")


def _entry(name):
    if not isinstance(name, str):
        return None
    wanted = name.strip().lower()
    return next((row for row in INFO["medications"]
                 if any(re.search(r"\b" + re.escape(alias) + r"\b", wanted) for alias in row["aliases"])), None)


def lookup(name, schedule=None):
    """Card data for the patient's own medication, or None when no medication is recorded."""
    if not name:
        return None
    entry = _entry(name)
    base = {"name": name, "schedule": schedule, "known": bool(entry), "topics": INFO["topics"],
            "content_status": INFO["content_status"], "source_label": INFO["source_label"]}
    if not entry:
        return {**base, "purpose": None, "how_to_take": None, "abstain": ABSTAIN_MEDICATION}
    return {**base, "name": entry["name"],
            "purpose": answer(entry["name"], "purpose", schedule),
            "how_to_take": answer(entry["name"], "how_to_take", schedule)}


def answer(name, topic_id, schedule=None):
    """Exact curated text for a topic, with the standard footer; abstention otherwise."""
    entry = _entry(name)
    if not entry:
        return ABSTAIN_MEDICATION
    if topic_id not in TOPIC_IDS:
        return ABSTAIN_TOPIC
    text = entry["answers"][topic_id].replace("{schedule}", schedule or "see your prescription label")
    return f"{text} {INFO['footer']}"


def mentions(text, term):
    return re.search(r"\b" + re.escape(term) + r"\b", text) is not None


def match_topic(question, own_medication):
    """Deterministic first pass: ('topic', id) | ('advice_request', None) | ('other_medication', None) | (None, None)."""
    text = (question or "").lower()
    if any(mentions(text, word) for word in CHANGE_WORDS):
        return "advice_request", None
    named = [row["name"] for row in INFO["medications"] if any(mentions(text, alias) for alias in row["aliases"])]
    own = _entry(own_medication)
    if any(mentions(text, word) for word in OTHER_MEDICATION_WORDS) or (named and (not own or any(n != own["name"] for n in named))):
        return "other_medication", None
    for topic_id, terms in KEYWORDS:
        if any(mentions(text, term) for term in terms):
            return "topic", topic_id
    return None, None


def classify(provider, question, own_medication):
    """Model fallback: choose one approved topic id, 'advice_request', 'other_medication' or 'none'. Never an answer."""
    from .tasks import structured_task
    result = structured_task(provider, "medication_topic", {
        "question": question, "patient_medication": own_medication,
        "topics": [{"id": topic["id"], "label": topic["label"]} for topic in INFO["topics"]]})
    choice = result.get("topic") if isinstance(result, dict) and set(result) == {"topic"} else None
    if choice in TOPIC_IDS:
        return "topic", choice
    if choice in {"other_medication", "advice_request"}:
        return choice, None
    return None, None
