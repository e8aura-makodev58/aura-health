# M6 — Patient Application

Status: PLANNED. Target: complete by 2026-10-07. May overlap late M5 work once backend/communication contracts stabilize.

## Goal and UX

Build a calm, sparse, mobile-first patient-facing hackathon web application on the accepted backend. Quiet when stable; context before conclusions; patient-initiated help always available. No risk dashboard, relapse probability, diagnostic score, streak guilt, gamified adherence, constant-monitoring claims, or nontransparent uncertainty.

## Minimum flows

1. **Stable home:** calm status, appropriate medication routine, optional check-in, non-alarming wearable/data state, and direct “talk to AURA” entry; do not fill empty space with irrelevant measurements.
2. **Good/Okay/Rough check-in:** under two minutes, structured first, optional safety-gated free text.
3. **Context clarification:** smallest useful question after backend-approved change; UI does not decide when to ask.
4. **Why AURA asked:** structured provenance—what changed, personal reference, known context, and what is *not* concluded.
5. **Explained/held:** patient adds explanation; observation remains visible/reviewable, repeat interruption decreases, anchor does not silently move.
6. **Medication routine:** acknowledged/missed/unknown recording and neutral support; no dose/taper control.
7. **Wearable unavailable:** missingness is not deterioration; return/re-establishment is communicated as uncertainty.
8. **Review preparation:** patient inspects structured snapshot; preparation does not automatically share.
9. **Safety:** render authoritative safety output; UI cannot downgrade or hide it.
10. **Patient-initiated interaction:** remains available even when current decision is STAY_QUIET.

A responsive phone-sized web app is sufficient; native mobile development is not required. Accessibility baseline: usable contrast, scalable text, keyboard navigation, non-color-only states, and plain language.

Frontend may collect, display, call APIs, and keep presentation state. It may not calculate drift, move anchors, assign safety tiers, infer diagnosis, or decide escalation.

## Suggested acceptance tests (future UI-series)

- **UI1:** stable home has no mental-health risk score.
- **UI2–UI3:** check-in reaches API and optional free text is safety-gated.
- **UI4–UI5:** explanation reaches governed hold path, and held observation stays visible.
- **UI6–UI7:** missingness and REESTABLISHING are not presented as deterioration/diagnosis.
- **UI8–UI9:** no dose/taper control; frontend cannot override safety.
- **UI10–UI11:** snapshot is not automatically shared; “why asked” uses backend provenance.
- **UI12–UI13:** patient can initiate while STAY_QUIET; no relapse/risk percentage.
- **UI14–UI15:** Cases A–F can be shown and core phone-width flows remain usable.

Perform genuine M6 implementation with CodeBuddy and/or WorkBuddy; capture evidence during work. Stop when core patient flows and Cases A–F work through UI, frontend has no policy, safety wins, mobile demo is usable, and evidence exists.
