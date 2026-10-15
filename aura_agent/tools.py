"""Immutable, scoped fact retrieval. No model-supplied patient ID or write handle."""

from copy import deepcopy
from datetime import datetime, timedelta
from hashlib import sha256
import json
from statistics import median
from aura_longitudinal.baseline import robust_spread

from .roles import ROLE_TOOLS


class RecordTools:
    def __init__(self, evidence, role, *, window_days=56, recent_readings_days=7, checkin_days=7, withheld=frozenset()):
        """withheld: optional categories the patient has not shared with the clinician
        ("notes", "readings", "checkin_history"); their facts are never created."""
        self.role = role
        self.withheld = frozenset(withheld)
        self.facts = {}
        self.groups = {name: [] for name in ROLE_TOOLS[role]}
        self.required = set()
        self.delivered = {}
        self.evidence = evidence
        self.end = end = evidence["period"]["end"]
        self.coverage_thresholds = evidence.get('analysis_coverage_thresholds', {})
        self.keys = {f"k{index+1}": row for index, row in enumerate(evidence["signals"])}
        self.cutoff = cutoff = (datetime.fromisoformat(end) - timedelta(days=window_days-1)).date().isoformat() if end else ""

        def add(tool, source, text, *, signal=None, required=False, finding=None, at=None, category=None):
            if category in self.withheld:
                return
            fid = f"f{len(self.facts) + 1}"
            fact = {"fact_id": fid, "source_ref": source, "text": text, "signal": signal,
                    "finding": finding, "at": at, "key_id": active_key if signal else None}
            self.facts[fid] = fact
            self.groups[tool].append(fid)
            if required:
                self.required.add(fid)

        add("get_status", "committed:status", f"Recorded period ends {end or 'with no entries'}. Current communication decision: {evidence['current_decision']}.")
        if evidence.get("record_coverage"):
            c = evidence["record_coverage"]
            add("get_status", "committed:coverage", f"Record coverage: last medication-routine record {c['last_medication_day'] or 'none'}; "
                f"{c['reported_later_in_window']} of the last {c['window_days']} days reported later; last check-in {c['last_checkin_day'] or 'none'}; "
                f"latest wearable day {c['last_wearable_day'] or 'none'}.")
        active_key = None
        for active_key, signal in self.keys.items():
            key, label = signal["key"], signal["label"]
            current = signal["current"] or {}
            enabled = signal.get("registry", {}).get("enabled_in_engine", True)
            add("get_status", f"baseline:{key['signal']}:{key['source']}:{key['metric']}",
                (f"{label}: sensing {current.get('sensing_state', 'UNOBSERVED')}; reference trust {current.get('trust_state', 'PROVISIONAL')}."
                 if enabled else f"{label}: display-only measurements; no current engine baseline or drift decision."),
                signal=key["signal"])
            for finding in signal["findings"]:
                if finding["last_seen"][:10] < cutoff:
                    continue
                drift = finding["drift"]
                delta = drift.get("current_vs_rolling") if drift["kind"] == "TRANSIENT_DEVIATION" else drift.get("rolling_vs_anchor")
                direction = ("LATER" if (delta or 0) > 0 else "EARLIER") if key["signal"] == "SLEEP_MIDPOINT" else ("HIGHER" if (delta or 0) > 0 else "LOWER")
                add("get_series", finding["event_id"],
                    f"{label}: {drift['description']} First recorded {finding['first_seen'][:10]}; last recorded {finding['last_seen'][:10]}.",
                    signal=key["signal"], required=True,
                    finding={"signal": key["signal"], "direction": direction, "since": finding["first_seen"][:10]}, at=finding["last_seen"][:10])
                self.facts[f'f{len(self.facts)}']['comparison'] = (
                    'RECENT_PATTERN' if drift['kind'] == 'TRANSIENT_DEVIATION' else 'PERSONAL_REFERENCE')
                self.facts[f'f{len(self.facts)}']['magnitude'] = {'value':delta, 'unit':signal['unit'],
                    'field':'current_vs_rolling' if drift['kind'] == 'TRANSIENT_DEVIATION' else 'rolling_vs_anchor'}
                metrics = []
                for field, title in (("current_vs_rolling", "current versus rolling deviation"), ("rolling_vs_anchor", "rolling versus own reference deviation"), ("trend_magnitude_per_day", "stored trend magnitude per day")):
                    value = drift.get(field)
                    if value is not None:
                        metrics.append(f"{title} {value:.3f} {signal['unit']}")
                if metrics:
                    add("get_series", finding["event_id"], f"{label}, recorded {finding['last_seen'][:10]}: " + "; ".join(metrics) + ".", signal=key["signal"], at=finding["last_seen"][:10])
            # Returned measurements are a bounded sample, explicitly not the entire
            # window. No new statistics, drift computation or missing-value filling.
            rows = [row for row in signal["observations"] if row["day"] >= cutoff and not row["deferred"]]
            for row in rows[-8:]:
                add("get_series", row["event_id"], f"{label} recorded {row['day']}: {row['value']} {signal['unit']}.", signal=key["signal"], at=row["day"], category="readings")
            if not enabled and signal.get('registry', {}).get('display', True) and end and "readings" not in self.withheld:
                start = (datetime.fromisoformat(end).date() - timedelta(days=recent_readings_days-1)).isoformat()
                threshold = self.coverage_thresholds.get(key['signal'], {}).get('minimum_observation_coverage', .5)
                recent = sorted((row for row in signal['observations'] if not row['deferred']
                    and min(row['coverage'],row['data_quality']) >= threshold and start <= row['day'] <= end[:10]),
                    key=lambda row:(row['day'],row.get('commit_order',0),row['event_id']))
                if recent:
                    latest = recent[-1]
                    values = [row['value'] for row in recent]
                    add('get_series',latest['event_id'],
                        f"{label}: {len(recent)} readings from {recent[0]['day']} to {latest['day']}; latest {latest['value']} {signal['unit']}; range {min(values)} to {max(values)} {signal['unit']}.",
                        signal=key['signal'],at=latest['day'])
                    fact = self.facts[f'f{len(self.facts)}']
                    fact['reading'] = {'label':label,'unit':signal['unit'],'count':len(recent),
                        'latest':latest['value'],'minimum':min(values),'maximum':max(values),
                        'start':recent[0]['day'],'end':latest['day'],'window_days':recent_readings_days}
                    fact['reading_source_refs'] = [row['event_id'] for row in recent]
            for row in signal["gaps"]:
                if row["at"][:10] >= cutoff:
                    add("get_gaps", row["event_id"], f"{label}: {row['type']} recorded {row['at'][:10]}.", signal=key["signal"], at=row["at"][:10])
            for row in signal["contexts"]:
                start = row.get("start") or ""
                finish = row.get("end")
                if finish and finish[:10] < cutoff:
                    continue
                # Arbitrary explanation text is deliberately excluded. Category and
                # explicit signal association are observable structured data.
                add("get_context", row["event_id"], f"{label}: {row['category']} context recorded from {start[:10]} to {finish[:10] if finish else 'no recorded end'}; explicitly associated with {label}.", signal=key["signal"])
                self.facts[f'f{len(self.facts)}']['context_span'] = {'start':start[:10], 'end':finish[:10] if finish else (end or '')[:10]}
                if row["event_id"] in evidence.get("agent_assessed_context_ids", []) and row.get("explanation"):
                    note = str(row["explanation"])[:400]
                    add("get_context", row["event_id"], f"{label}: patient-reported context: {json.dumps(note)}.", signal=key["signal"], category="notes")
        for row in evidence["checkins"][-8:]:
            if not row["deferred"] and row["at"][:10] >= cutoff:
                add("get_decisions", row["event_id"], f"Patient check-in {row['at'][:10]}: {row['state']}.", category="checkin_history")
        # One answer per recorded calendar day; held answers and missing days
        # cannot extend a run. Latest committed answer wins within the day.
        days = {}
        for row in sorted(evidence['checkins'], key=lambda row: row['at']):
            if not row['deferred'] and cutoff <= row['at'][:10] <= (end or '')[:10]:
                days[row['at'][:10]] = row
        runs = []
        for day, row in sorted(days.items()):
            if (runs and runs[-1]['state'] == row['state'] and
                    (datetime.fromisoformat(day)-datetime.fromisoformat(runs[-1]['end'])).days == 1):
                runs[-1]['end'] = day
                runs[-1]['source_refs'].append(row['event_id'])
            else:
                runs.append({'state':row['state'], 'start':day, 'end':day, 'source_refs':[row['event_id']]})
        for run in runs:
            add('get_decisions', run['source_refs'][-1],
                f"Patient-reported check-ins: {run['state']} on {len(run['source_refs'])} consecutive recorded days, from {run['start']} to {run['end']}.", at=run['end'])
            self.facts[f'f{len(self.facts)}']['checkin_run'] = run
        if days and end:
            start = (datetime.fromisoformat(end)-timedelta(days=checkin_days-1)).date().isoformat()
            recent = [row for day,row in sorted(days.items()) if day >= start]
            if recent:
                state = recent[-1]['state']
                count = sum(row['state'] == state for row in recent)
                latest_run = runs[-1]
                add('get_decisions', recent[-1]['event_id'],
                    f"Patient-reported check-ins: {state} on {count} of the last {checkin_days} days; {len(recent)} days recorded. Latest run: {len(latest_run['source_refs'])} consecutive days from {latest_run['start']} to {latest_run['end']}.", at=recent[-1]['at'][:10])
                self.facts[f'f{len(self.facts)}']['checkin_summary'] = {'state':state,'count':count,
                    'window_days':checkin_days, 'recorded_days':len(recent), 'start':start, 'end':end[:10],
                    'run_start':latest_run['start'], 'run_end':latest_run['end'],
                    'run_days':len(latest_run['source_refs']), 'source_refs':[row['event_id'] for row in recent]}
        for row in sorted(evidence["medication"], key=lambda r: r.get("day") or r["at"][:10])[-8:]:
            day = row.get("day") or row["at"][:10]
            if not row["deferred"] and day >= cutoff:
                later = f" (reported later on {row['at'][:10]})" if row.get("reported_later") else ""
                add("get_decisions", row["event_id"], f"Medication-routine record {day}: {row['status']}{later}.")
        for row in evidence["held"]:
            active_key = next((key for key, s in self.keys.items() if s['key']['signal']==row['signal'] and s['key']['source']==row['source'] and (s['key'].get('metric') or '')==(row.get('metric') or '')), None)
            add("get_review_snapshot", f"held:{row['signal']}:{row['source']}:{row['direction']}",
                f"{row['signal']}: {row['status']}. Explanation retained for review; own reference unchanged.", signal=row["signal"], required=True)
        add("get_review_snapshot", "committed:review", "Review draft status: Not sent.")
        for row in evidence.get("assessed_notes", []):
            add("get_context", row["event_id"], f"Patient note {row['at'][:10]}: {json.dumps(row['text'][:400])}.", category="notes")
        if self.withheld:
            # Say so where the data would be, so an agent looking for it can cite the reason.
            names = {"notes": ("get_context", "the patient's notes (their own words)"),
                     "readings": ("get_series", "detailed wearable readings (daily values)"),
                     "checkin_history": ("get_decisions", "each day's check-in entry (summaries remain)")}
            for category, (tool, label) in names.items():
                if category in self.withheld:
                    add(tool, f"sharing:withheld:{category}", f"Not shared with the clinician by the patient: {label}. Not available in this record; ask the patient directly if relevant.")
        if evidence.get("activity_summary"):
            add("get_context", evidence["activity_summary"]["ref"], evidence["activity_summary"]["text"])
        from .voice import prepare_fact
        from .roles import AgentRole
        for fact in self.facts.values():
            prepare_fact(fact, self.keys, role == AgentRole.PATIENT_INSIGHT)

    def specs(self):
        specs = []
        for name in self.groups:
            props = {}
            if name == "summarize_checkins":
                specs.append({"type": "function", "function": {"name": name,
                    "description": "Calculate check-in counts, coverage and percentages. Use last_days with null start/end for an inclusive window ending on the latest recorded patient-local date, or explicit ISO start/end with null last_days. Latest non-held report per local day wins; absent days remain unknown. State is Good, Okay or Rough. Default denominator: recorded_days; calendar_days reports the fraction explicitly recorded as that state, not the state of missing days. Cite the returned fact and copy its display text for a percentage answer. Call twice for period comparisons; do not calculate new numbers yourself.",
                    "strict": True, "parameters": {"type": "object", "additionalProperties": False,
                        "required": ["start", "end", "last_days", "state", "denominator"],
                        "properties": {"start": {"type": ["string", "null"]}, "end": {"type": ["string", "null"]},
                            "last_days": {"type": ["integer", "null"], "minimum": 1, "maximum": 56},
                            "state": {"type": "string", "enum": ["Good", "Okay", "Rough"]},
                            "denominator": {"type": "string", "enum": ["recorded_days", "calendar_days"]}}}}})
                continue
            if name in {"get_series", "get_context", "get_gaps"}:
                props = {"key_id": {"type": ["string", "null"], "enum": [*self.keys, None]},
                         "start": {"type": ["string", "null"]}, "end": {"type": ["string", "null"]}}
            if name in {"compare_windows", "day_of_week", "summarize_gaps"}:
                props = {"key_id": {"type": "string", "enum": list(self.keys)},
                         "start": {"type": "string"}, "end": {"type": "string"}}
                if name == "compare_windows":
                    props.update(previous_start={"type": "string"}, previous_end={"type": "string"})
            specs.append({"type": "function", "function": {"name": name,
                "description": f"Read-only {name}. Available keys: " + json.dumps({key: row["label"] for key, row in self.keys.items()}) +
                    f". Dates are ISO; allowed analysis dates {self.cutoff} through {(self.end or '')[:10]}. Statistics use actual covered days, separately per source/metric. get_series includes retained findings; brief/visit must retrieve all keys with key_id=null.",
                "strict": True, "parameters": {"type": "object", "properties": props, "required": list(props), "additionalProperties": False}}})
        return specs

    def call(self, name, arguments):
        if name not in self.groups or not isinstance(arguments, dict):
            raise ValueError("UNAUTHORIZED_TOOL")
        allowed = {key for spec in self.specs() if spec["function"]["name"] == name for key in spec["function"]["parameters"]["properties"]}
        if set(arguments) - allowed: raise ValueError("UNAUTHORIZED_TOOL")
        if name == "summarize_checkins":
            if not arguments:
                return {"facts": [], "error": "WINDOW_REQUIRED", "scope": "explicit window and category arguments required"}
            from .checkin_analysis import summarize
            fact = summarize(self.evidence, arguments, self.cutoff, f"f{len(self.facts)+1}")
            self.facts[fact['fact_id']] = fact
            self.delivered[fact['fact_id']] = fact
            return {"facts": [{**fact, "source_refs": ["ref:" + sha256(ref.encode()).hexdigest()[:16]
                                                       for ref in fact['source_refs']]}],
                    "scope": "deterministic descriptive calculation; patient-local days; missing is unknown"}
        if name in {"compare_windows", "day_of_week", "summarize_gaps"}:
            if not arguments: return {"facts": [], "scope": "explicit window arguments required"}
            return self._analysis(name, arguments)
        facts = [deepcopy(self.facts[fid]) for fid in self.groups[name]]
        if arguments:
            key = arguments.get("key_id")
            if key is not None:
                if key not in self.keys: raise ValueError("UNAUTHORIZED_TOOL")
                facts = [fact for fact in facts if fact["key_id"] == key]
            start, end = arguments.get("start"), arguments.get("end")
            if start is not None or end is not None:
                self._window(start, end)
                facts = [fact for fact in facts if fact["at"] is None or start <= fact["at"] <= end]
        def model_projection(fact):
            from .roles import AgentRole
            # These fields are presentation-only copies kept for UI disclosure.
            # Budget the actual model payload, not duplicates never sent to it.
            excluded = {'reading_source_refs','raw_text'}
            if self.role != AgentRole.PATIENT_INSIGHT:
                excluded.update({'patient','magnitude'})
            model_fact = {**{k:v for k,v in fact.items() if k not in excluded},
                          'source_ref':'ref:' + sha256(fact['source_ref'].encode()).hexdigest()[:16]}
            for field in ('checkin_run','checkin_summary'):
                if field in model_fact:
                    model_fact[field] = {k:v for k,v in model_fact[field].items() if k != 'source_refs'}
            return model_fact

        while len(json.dumps([model_projection(fact) for fact in facts])) > 24000:
            # Keep the compact recent check-in view when a fragmented window
            # has many runs; retained findings keep the same mandatory budget.
            latest_run = next((fact['fact_id'] for fact in reversed(facts) if fact.get('checkin_run')),None)
            removable=next((index for index in range(len(facts)-1,-1,-1)
                if facts[index]['fact_id'] not in self.required and not facts[index].get('checkin_summary')
                and facts[index]['fact_id'] != latest_run),None)
            if removable is None:raise ValueError('TOOL_BUDGET')
            facts.pop(removable)
        self.delivered.update({fact["fact_id"]: fact for fact in facts})
        # Demo event IDs can encode scenario names. The model receives opaque
        # reference aliases, while application/UI citations retain real source IDs.
        model_facts = [model_projection(fact) for fact in facts]
        return {"facts": model_facts, 'retained_fact_ids':sorted(self.required & {fact['fact_id'] for fact in facts}), "scope": "selected record; selected window; bounded measurement sample"}

    def _window(self, start, end):
        from datetime import date
        if not isinstance(start, str) or not isinstance(end, str): raise ValueError("WINDOW_REQUIRED")
        a, b = date.fromisoformat(start), date.fromisoformat(end)
        if a > b or (b-a).days >= 180 or not self.end or end > self.end[:10] or start < self.cutoff:
            raise ValueError("WINDOW_BUDGET")

    def _analysis(self, name, args):
        self._window(args.get("start"), args.get("end"))
        key = args.get("key_id")
        if key not in self.keys: raise ValueError("UNAUTHORIZED_TOOL")
        signal = self.keys[key]
        threshold=self.coverage_thresholds.get(signal['key']['signal'], {}).get('minimum_observation_coverage', .5)
        quality=threshold
        def rows(start, end):
            by_day = {}
            for row in signal["observations"]:
                if row["deferred"] or row["coverage"] < threshold or row["data_quality"] < quality or not start <= row["day"] <= end: continue
                prior = by_day.get(row["day"])
                if prior is None or (row["coverage"]*row["data_quality"], row.get("commit_order", 0)) >= (prior["coverage"]*prior["data_quality"], prior.get("commit_order", 0)):
                    by_day[row["day"]] = row
            return list(by_day.values())
        selected = rows(args["start"], args["end"])
        data = {"start": args["start"], "end": args["end"], "covered_days": len(selected)}
        def stats(items):
            vals = tuple(row["value"] for row in items)
            return {"count": len(vals), "median": round(median(vals), 3) if vals else None,
                    "robust_spread": round(robust_spread(vals), 3) if vals else None}
        if name == "compare_windows":
            self._window(args.get("previous_start"), args.get("previous_end"))
            previous = rows(args["previous_start"], args["previous_end"])
            data.update(recent=stats(selected), previous=stats(previous), previous_start=args["previous_start"], previous_end=args["previous_end"])
            selected += previous
        elif name == "day_of_week":
            data["days"] = {str(index): stats([row for row in selected if datetime.fromisoformat(row["day"]).weekday() == index]) for index in range(7)}
        else:
            total = (datetime.fromisoformat(args["end"])-datetime.fromisoformat(args["start"])).days+1
            data.update(calendar_days=total, missing_days=total-len(selected))
        fid = f"f{len(self.facts)+1}"
        refs = sorted({row["event_id"] for row in selected})
        fact = {"fact_id": fid, "source_ref": "analysis:" + sha256(json.dumps(args, sort_keys=True).encode()).hexdigest()[:16],
                "text": signal["label"] + ": " + json.dumps(data, sort_keys=True) + " " + signal["unit"],
                "signal": signal["key"]["signal"], "finding": None, "at": args["end"], "source_refs": refs,
                "analysis": data}
        self.facts[fid] = fact; self.delivered[fid] = fact
        model = {**fact, "source_refs": ["ref:"+sha256(ref.encode()).hexdigest()[:16] for ref in refs]}
        return {"facts": [model], "scope": "descriptive analysis, not engine policy"}
