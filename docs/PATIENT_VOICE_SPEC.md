# Patient voice spec: warm, plain, still grounded (for Codex)

2026-10-11. Claude. **User direction (2026-10-11):** the patient summary is cold, technical
and robotic and is not acceptable; make aura-agent smarter by giving it sample remarks as
context. This spec adds the samples and fixes the code paths that produce the cold text.
It does not relax any safety or grounding rule.

## 1. What produced the text the user rejected
The pasted block had four separate causes:
1. **Raw fact text reaches the patient.** "Sleep midpoint is later relative to the anchored
   reference. First recorded 2026-02-23; last recorded 2026-03-11." is the engine's
   `drift['description']` embedded in the fact (`aura_agent/tools.py`) and shown in the
   "Why this summary?" panel. Same for "Rough on 20 consecutive recorded days, from
   2026-02-20 to 2026-03-11" (`tools.py:120`).
2. **Internal source IDs are shown** ("Source: demo-B-7-69-checkin").
3. **A repeated caveat line:** "AI draft from synthetic records — check the linked
   sources." (`aura_app/agent.py:164`) plus the chip. DECISIONS §44 says no recurring
   caveats; the chip alone is enough.
4. **The prompt itself forbids warmth.** `patient_insight/SKILL.md` says one sentence of up
   to 20 words, "no reassurance, advice or tasks", "copy the exact ISO date", "no rounding".
   The model is told to be a robot, so it is one.

## 2. Voice rules (patient-facing text, all surfaces)
- Second person, everyday words, short sentences (aim ≤16 words, never more than 25).
- Start from what the person told us or what they would recognise ("Your check-ins", "You've
  been sleeping later"), not from a measurement name.
- Time in human terms ("since late February", "for about three weeks", "over the last
  few days"), never ISO dates. Rounded quantities in everyday units ("about three hours
  later"). Exact values live behind "Why?" for people who want them.
- Acknowledge the person's own reports without judging how they feel: "You've marked most
  days as Rough." Never "you feel/are", never "I'm sorry you're struggling".
- Offer, never instruct: "If you'd like, you can add a note about what's been going on, or
  get your appointment summary ready." One offer at most, and only when something changed.
- Warm means calm and human, not cheerful. No exclamation marks, emoji or cheerleading.
- Still forbidden: diagnosis, prediction, cause ("because", "due to"), treatment or
  medication advice, "normal/healthy/good/bad", scores, reassurance about safety or mental
  state, urgency. Safety wording is pinned UI, never generated.

## 3. Sample remarks (style references; wording is not to be copied)
Use as few-shot context. Each example shows facts → remark. Facts are placeholders, so
the model cannot copy numbers or dates; every real claim must still be grounded.

| Situation | Remark |
|---|---|
| Sleep later + check-ins Rough (Case B) | "Over the past few weeks you've been sleeping later than usual, and you've marked most days as Rough. Your activity has also dipped since early March." |
| Same, with offer | "The last three weeks have looked different from your usual: later nights, less activity, and a lot of Rough days in your check-ins. If you'd like, we can add this to your appointment summary." |
| Short-term change (flu-like channels) | "In the last few days your resting heart rate, breathing and temperature readings have all moved up, and you've been less active. Before that, things looked steady." |
| One change only | "Your sleep has been later than usual since late February. Nothing else has moved." |
| Steady | "Nothing has moved away from your usual lately. Your sleep and activity look much like they have." |
| Data gap | "Your watch hasn't sent data since 8 March, so this picture is a little incomplete." |
| Check-ins only | "You've marked the last twenty days as Rough. That's yours to share or not; we can note it for your appointment if you want." |
| Context added | "You mentioned travelling in mid-March, and your sleep has been later since then." — only when the patient's own recorded context is explicitly associated with the signal (never inferred) |

Bad → good (from the rejected text):
- "Your sleep time was later than usual, and you reported Rough days." →
  "You've been sleeping later than usual, and you've marked most days as Rough."
- "Sleep midpoint is later relative to the anchored reference. First recorded 2026-02-23…" →
  (Why panel) "Your usual bedtime has shifted later, by about three hours, since late February."
- "Rough on 20 consecutive recorded days, from 2026-02-20 to 2026-03-11. Source: demo-B-7-69-checkin"
  → "You marked 'Rough' on 20 days in a row (20 Feb – 11 Mar). From: your check-ins."

## 4. Implementation
1. **Examples file.** `aura_agent/voice_examples.json` (versioned, short, 6–8 entries
   from section 3 with placeholders). The patient_insight prompt loads it as "style
   examples; never copy wording, numbers or dates; every claim must come from the
   cited facts". Rotate or shuffle the order so output is not one repeated phrasing.
2. **Friendly facts for the patient role.** The server adds, per finding, friendly
   fields (`since_phrase`, `duration_phrase`, `magnitude_phrase`) computed
   deterministically, and the patient role's fact text uses them instead of engine
   descriptions. The verifier checks the model's wording against these facts. Numbers and
   dates in the model's text are then rare; the existing numeric/date checks stay as they
   are, and the SKILL no longer asks for ISO dates.
3. **Rewrite `patient_insight/SKILL.md`:** two or three short sentences (≤ 35 words total),
   allow one gentle offer, allow acknowledging reported check-ins as the person's own
   reports, keep every prohibition in section 2. Update the headline length limit for the
   patient role accordingly (validator rule changed only for length, nothing else).
4. **Same voice in the fallback.** The deterministic patient templates
   (`aura_agent/templates.py`) are what most viewers see when the model is skipped; rewrite
   them from `voice_examples` patterns using the friendly fields, so cold wording is gone
   with the model off.
5. **"Why this summary?" panel (patient):** three plain lines: "What we looked at", "What we
   saw", "Where it comes from" (friendly labels such as "Your check-ins, 20 Feb – 11 Mar";
   no engine descriptions, no internal IDs, no jargon). Exact values and raw source IDs
   only in the clinician view or an explicit "Technical details" fold.
6. **Remove** "AI draft from synthetic records — check the linked sources." from patient
   and clinician surfaces; keep the chip.
7. **Clinician view** keeps its own register (concise, factual). Do not copy the warm
   voice there.

## 5. Acceptance
- A deterministic test over the patient surfaces (recap, cards, Why panel, offline
  fallback) in cases A–F and after each simulator event: no ISO dates, no source IDs, no
  words from the jargon list (anchored, midpoint, rolling, deviation, extraction,
  baseline, drift, consecutive, recorded days), no exclamation marks, mean sentence length
  ≤ 16 words.
- Prohibited-claim, cause-language and fabricated-number tests still pass unchanged;
  an exemplar-copying test shows placeholder numbers never appear in output.
- **User sign-off gate:** before WP4 is called complete, show the user five real outputs
  (Case B, flu, stable, gap, check-ins only) from the live app and the offline fallback,
  and record whether they accept the voice. The user's judgment is the criterion here.
- Same facts still produce the same set of cited facts; the cards are unchanged.

## 6. Risks
- Warmth can drift toward reassurance or implied feeling. Keep the prohibition list in
  the validator, and treat check-in answers only as attributed reports.
- Friendly phrases ("about three weeks") are computed approximations; the semantic
  verifier and tests must check them against the exact values.
- Example copying: use placeholders, rotate order, and cap exemplars at eight.
