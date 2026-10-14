"""Patient-reported activities from safety-cleared notes.

The agent only proposes tags; deterministic checks decide what is kept: a fixed category list,
the phrase must appear verbatim in the note, and a duration is kept only when the note states
it (number + unit). Details stay on the patient side; clinicians receive aggregates only.
No scoring, interpretation or clinical inference.
"""
from datetime import date, timedelta
import re

CATEGORIES = ("physical", "social", "creative", "restful", "outdoors")
LABELS = {"physical": "Physical", "social": "Social", "creative": "Creative / hobbies",
          "restful": "Restful", "outdoors": "Outdoors"}
MAX_ITEMS = 5
_UNIT = r"(hours?|hrs?|h|minutes?|mins?|m)\b"
_STATED = re.compile(r"(\d+(?:\.\d+)?)\s*" + _UNIT, re.IGNORECASE)


def _stated_minutes(text):
    """Durations written in the note itself, in minutes."""
    found = set()
    for number, unit in _STATED.findall(text):
        value = float(number) * (60 if unit.lower().startswith("h") else 1)
        if 0 < value <= 24 * 60:
            found.add(round(value))
    return found


def check(note, proposal):
    """Keep only verifiable items from an agent proposal; never raises."""
    if not isinstance(proposal, dict) or set(proposal) != {"activities"} or not isinstance(proposal["activities"], list):
        return []
    stated, lowered, kept = _stated_minutes(note), note.lower(), []
    for item in proposal["activities"][:MAX_ITEMS]:
        if not isinstance(item, dict) or set(item) - {"phrase", "categories", "minutes"}:
            continue
        phrase, categories, minutes = item.get("phrase"), item.get("categories"), item.get("minutes")
        if not isinstance(phrase, str) or not 2 <= len(phrase.strip()) <= 120 or phrase.strip().lower() not in lowered:
            continue
        if not isinstance(categories, list) or not categories:
            continue
        categories = [c for c in dict.fromkeys(categories) if c in CATEGORIES]
        if not categories:
            continue
        if not (type(minutes) is int and minutes in stated):
            minutes = None
        kept.append({"phrase": phrase.strip(), "categories": categories, "minutes": minutes})
    return kept


def extract(provider, note):
    from .tasks import structured_task
    proposal = structured_task(provider, "activity_extract",
                               {"note": note, "categories": list(CATEGORIES)}, reasoning="low")
    return check(note, proposal)


def summarize(rows, end, days=14):
    """Aggregate per category for the last `days` of the record vs the `days` before. No phrases."""
    recent_from = end - timedelta(days=days - 1)
    earlier_from, earlier_to = recent_from - timedelta(days=days), recent_from - timedelta(days=1)
    def window(start, finish):
        out = {c: {"days": set(), "minutes": 0} for c in CATEGORIES}
        for row in rows:
            day = date.fromisoformat(row["at"][:10])
            if start <= day <= finish:
                for item in row["items"]:
                    for c in item["categories"]:
                        out[c]["days"].add(day)
                        out[c]["minutes"] += item["minutes"] or 0
        return {c: {"days": len(v["days"]), "minutes": v["minutes"]} for c, v in out.items()}
    recent, earlier = window(recent_from, end), window(earlier_from, earlier_to)
    categories = [{"category": c, "label": LABELS[c], "recent": recent[c], "earlier": earlier[c]}
                  for c in CATEGORIES if recent[c]["days"] or earlier[c]["days"]]
    return {"recent": {"start": recent_from.isoformat(), "end": end.isoformat()},
            "earlier": {"start": earlier_from.isoformat(), "end": earlier_to.isoformat()},
            "notes_considered": sum(1 for row in rows if earlier_from <= date.fromisoformat(row["at"][:10]) <= end),
            "categories": categories}


def _days(n):
    return f"{n} day" if n == 1 else f"{n} days"


def hours(minutes):
    return f"{minutes / 60:g} h" if minutes % 60 == 0 or minutes >= 60 else f"{minutes} min"


def summary_text(summary):
    """One factual sentence for the clinician agent; aggregates only, no note content."""
    if not summary["categories"]:
        return (f"Patient-reported activity from notes, {summary['recent']['start']} to {summary['recent']['end']}: "
                "no activities mentioned. Note contents stay with the patient.")
    parts = []
    for row in summary["categories"]:
        r, e = row["recent"], row["earlier"]
        part = f"{row['label']}: mentioned on {_days(r['days'])} vs {_days(e['days'])}"
        if r["minutes"] or e["minutes"]:
            part += f", stated time {hours(r['minutes'])} vs {hours(e['minutes'])}"
        parts.append(part)
    return (f"Patient-reported activity from notes, {summary['recent']['start']} to {summary['recent']['end']} "
            f"vs {summary['earlier']['start']} to {summary['earlier']['end']}: " + "; ".join(parts) +
            ". Aggregates only; note contents stay with the patient.")
