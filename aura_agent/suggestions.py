"""Curated, optional suggestions after a recorded change. Never AI-written, never about medication,
never shown while safety is not normal."""

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
