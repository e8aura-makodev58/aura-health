"""Curated, optional suggestions after a recorded change. Never about medication, never shown while
safety is not normal. The ideas themselves always come from the curated catalogue; a live agent may
choose among them for this person and write a short checked line about why (fallback: rule order)."""

import json
from datetime import date, timedelta
from pathlib import Path

CATALOG = json.loads(Path(__file__).with_name("suggestions.json").read_text())


def _direction(signal, drift):
    delta = drift.get("current_vs_rolling") if drift.get("kind") == "TRANSIENT_DEVIATION" else drift.get("rolling_vs_anchor")
    if signal == "SLEEP_MIDPOINT":
        return "LATER" if (delta or 0) > 0 else "EARLIER"
    return "HIGHER" if (delta or 0) > 0 else "LOWER"


def _since_phrase(day):
    when = date.fromisoformat(day[:10])
    part = "early" if when.day <= 10 else "mid" if when.day <= 20 else "late"
    return f"{part} {when.strftime('%B')}"


def select(evidence, safety_normal):
    """Return {because, trigger, options} for the most relevant recent change, or None."""
    if not safety_normal or not evidence or not (evidence.get("period") or {}).get("end"):
        return None
    end = date.fromisoformat(evidence["period"]["end"][:10])
    recent_from = (end - timedelta(days=CATALOG["recent_days"] - 1)).isoformat()
    found = {}
    for row in evidence.get("signals", []):
        signal = row["key"]["signal"]
        for finding in row.get("findings", []):
            if finding["last_seen"][:10] < recent_from:
                continue
            key = f"{signal}:{_direction(signal, finding['drift'])}"
            if key in CATALOG["by_change"] and (key not in found or finding["first_seen"] > found[key]["first_seen"]):
                found[key] = {**finding, "transient": finding["drift"].get("kind") == "TRANSIENT_DEVIATION"}
    key = next((k for k in CATALOG["priority"] if k in found), None)
    if key is None:
        return None
    change, finding = CATALOG["by_change"][key], found[key]
    reference = "than in your recent records" if finding["transient"] else "than your usual"
    subject = change["subject"]
    because = f"{subject} {reference} since {_since_phrase(finding['first_seen'])}."
    options = [change["option"]] + [row for row in CATALOG["general"] if row["id"] != change["option"]["id"]][:2]
    signal, direction = key.split(":")
    return {"because": because, "trigger": {"signal": signal, "direction": direction, "since": finding["first_seen"][:10]},
            "options": options}


POOL = {row["id"]: row for row in CATALOG["pool"]}
FIXED_ACK = "Noted for today. Go at your own pace."


def personalize(provider, base, notes):
    """Agent pick from the curated pool for this change and the person's recent notes.

    Returns {"options": [...], "why": str} or None (caller keeps the rule-based ideas)."""
    from aura_communication.validation import patient_text_problems
    from .tasks import structured_task
    result = structured_task(provider, "suggestion_pick", {
        "recorded_change": base["because"], "recent_notes": notes,
        "ideas": [{"id": row["id"], "label": row["label"]} for row in CATALOG["pool"]]}, reasoning="low")
    if not isinstance(result, dict) or set(result) != {"ids", "why"} or not isinstance(result["ids"], list):
        return None
    ids = [item for item in dict.fromkeys(result["ids"]) if isinstance(item, str) and item in POOL][:3]
    if not ids or len(ids) != len(result["ids"][:3]) or patient_text_problems(result["why"], 140, 2):
        return None
    return {"options": [POOL[item] for item in ids], "why": result["why"].strip()}


def acknowledge(provider, option):
    """One short checked sentence about the person's choice, or None (caller uses FIXED_ACK)."""
    from aura_communication.validation import patient_text_problems
    from .tasks import structured_task
    result = structured_task(provider, "suggestion_ack", {"chosen_idea": option["label"]}, reasoning="low")
    message = result.get("message") if isinstance(result, dict) and set(result) == {"message"} else None
    return None if patient_text_problems(message, 140, 2) else message.strip()
