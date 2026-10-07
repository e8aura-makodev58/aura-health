# Patient experience redesign

Status: implemented on 2026-10-07, but the user subsequently found the experience
unintuitive and overwhelming. **Not accepted as a satisfactory patient experience.**
Further implementation is paused for joint product reassessment with Claude; see
[discussion brief](PRODUCT_REASSESSMENT.md). Technical checks below are not usability
validation. The original dedicated UI/UX review below informed the work.
No additional synthetic data/scenarios. Accepted safety and longitudinal engines,
application API and database schema remain unchanged.

## Delivered implementation

- Compact Today interaction state, optional one-tap check-in and expandable medication
  record; quiet wording describes communication, never a health/safety assessment.
- Today / Patterns / Review navigation; About/privacy and gear in header. Persistent
  Talk action on every view. Mobile bottom dock; laptop navigation rail and reading column.
- Expandable signal rows; descriptive observations stay visible in row summaries;
  numeric/reference provenance is one level deeper. Held changes retain explanations,
  unchanged-reference wording and review availability. No browser trend calculation.
- Review groups disclose details progressively, with temporary-preview limitations at
  the selection point. The backend snapshot and sharing behavior are unchanged.
- Hosted composer offers labelled examples, read-only exact input and explicit synthetic
  limitations; the non-hosted development note path remains available and safety-gated.
- Independent safety/resources remain on every view. The bounded, keyboard-focusable
  safety region scrolls on short screens rather than swallowing the whole viewport.
- Configured/live versus actual generated/fallback disclosure and gear settings retained.

Verification uses existing UI1–UI15/offline, hosted, settings and eight new UX browser
checks. Screenshots/results are generated under `/tmp/aura-redesign-browser-artifacts`;
run instructions: `aura_ui/README.md`. This is engineering UX verification, not clinical
validation or CodeBuddy evidence.

## Purpose

AURA should feel like a quiet companion around an existing treatment routine, not a
psychiatric dashboard or an unrestricted therapy chatbot. The patient should quickly
understand: is AURA asking me anything, can I record my routine, and can I initiate help?
Portrait mobile is the primary layout; laptop uses the same task hierarchy.

## Findings from the pre-redesign implementation

- `index.html`/`styles.css`: tall masthead, abstract headline and large cards consume
  the first phone screen; the primary patient-initiated entry is below them.
- Today offers multiple competing large actions instead of a clear state/message
  followed by small optional routine actions.
- `app.js` Patterns gives all four signals similar prominence and displays technical
  reference details immediately. That is inspectable but not a patient-centered summary.
- Review renders many groups/checklists; temporary checkboxes can resemble approval
  even though nothing is shared or saved as approval.
- Repeated engineering disclaimers compete with useful information. Keep essential
  notices visible; move detailed technical limits into accessible information/details.
- Hosted text composer suggests arbitrary input is supported when only named fixtures
  are accepted. The synthetic interaction should use clear example selection.
- Fixed “No live model” copy is unsuitable for a configurable synthetic AI demo;
  disclosure must reflect the actual provider and each response's recorded path.

## Information architecture

Three main views: **Today · Patterns · Review**. Information/privacy sits behind a
clearly labelled header control. **Talk to AURA** is persistently accessible as an
action across views, not buried in Today and not an always-on chatbot feed.
Demo controls remain separate, clearly labelled synthetic, and do not dominate the
patient navigation. Retain fixture dates so the UI does not imply live wearable data.

### Portrait: default quiet state

```text
┌──────────────────────────────────┐
│ AURA                 Information │
│ Synthetic demonstration          │
├──────────────────────────────────┤
│ Today             [fixture date] │
│                                  │
│ No question from AURA right now.  │
│ You can check in whenever useful. │
│                                  │
│ How are things?     [optional]    │
│ [ Good ] [ Okay ] [ Rough ]      │
│                                  │
│ Medication routine       Record ›│
│ Your recent context      Details›│
│                                  │
│ [ Talk to AURA                  ]│
├──────────────────────────────────┤
│ Today       Patterns      Review │
└──────────────────────────────────┘
```

The quiet statement describes communication, **not** a healthy/safe assessment.
When the server supplies an approved question, it occupies the central state area
and presents its smallest useful action plus “Why AURA asked.” No frontend determines
whether a question is warranted. Safety overrides this presentation and remains
visible across views; no dismiss/downgrade button is introduced.

### Laptop

A restrained navigation rail/header, comfortable central reading column and optional
secondary routine/context column. Do not stretch all cards edge-to-edge or turn the
laptop view into a sensor dashboard. Use the same actions/disclosures as mobile.

## Interaction design

**Today:** compact heading and state; optional one-tap check-in; routine row expands
to acknowledged/missed/not-sure. Recording feedback is clear and neutral, without
streaks, pressure or inferred medication instructions. Keep help within thumb reach.

**Patterns:** a plain-language overview of server-returned observations, then compact
signal rows. Expand to show observed change, personal reference period, coverage,
linked context and limits. Further “Technical details” contains numeric/statistical
values and explicit reference provenance. Do not calculate trends/relevance in JS.

**Explained change:** show the retained change and explanation together: “Explanation
saved for review.” Explain that repeated prompts for that same change are reduced
and the reference remains unchanged. A reopened item presents new evidence; it does
not imply the patient's explanation was dishonest or automatically rejected.

**Wearable gap/return:** “Wearable data unavailable,” then “Data has returned; the
reference is being re-established.” Missingness is neither normal nor pathological.
The absence of a governed REESTABLISHING exit stays inspectable in technical details;
presentation must not pretend the trust state has resolved.

**Review:** concise review-period overview; grouped relevant observations/context,
routine records, held items and questions; repetitive history progressively disclosed.
Selections labelled “Temporary preview” at the point of interaction. No Send/Approve
control until a governed sharing workflow exists. All retained data remains inspectable.

**Talk:** focused interaction surface, not a blank unrestricted chat. For this hosted
prototype, clearly named synthetic examples with exact submitted fixture text available
for inspection. Ordinary arbitrary public text must not be passed to a model. Live
wording only follows a completed gate and an approved intent. Do not imply unlimited
conversation when the model is choosing from bounded approved wording alternatives.

**Safety/offline:** authoritative output and independent resource panel remain visible
and reachable across navigation, including keyboard-open/short-height phone layouts.
Avoid a tall sticky region covering the entire screen. Any compact treatment must
retain policy-required wording/resources, not hide them in a dismissed accordion.
Fallback is honest; no emergency monitoring or contact/notification promise.

## Visual direction

Warm, calm, precise. Smaller functional headings, clear typographic hierarchy, generous
but economical spacing, restrained green/neutral palette. Icons have text labels;
no decorative diagnostic gauges or alarming risk gradients. Do not add animations,
illustrations or charts merely to fill an otherwise quiet state. Keep a persistent,
unambiguous synthetic-data label and accessible prototype limitations.

## Verification gate before deployment

- At 390×844 portrait, state, check-in entry and Talk are immediately reachable.
- No horizontal overflow at 320 px; laptop layout usable at 1280 px.
- Keyboard-open dialogs remain usable; safe-area navigation never obscures actions.
- At least 44 px action targets; readable text, visible focus, keyboard navigation,
  semantic headings and non-color-only state distinctions.
- Stable/change/held/gap/return/safety/offline displays agree with server state.
- Safety output/resources remain accessible on every view; no tier/diagnosis/score UI.
- Provider disclosure distinguishes configured live synthetic wording, static policy
  and per-response fallback; never claims successful generation just from configuration.
- Institution-hosted deployment remains intended future architecture, not readiness.
- Explicit context/provenance and existing commands retained; no browser domain policy.
- Honest temporary review selection and synthetic-only composer; no implied sharing.
- Existing acceptance and real-browser tests remain green; update assertions to test
  preserved behavior rather than preserve obsolete visual structure.

## Implementation order

1. Align on this task structure and information hierarchy.
2. Wire synthetic-only live provider and truthful configuration/output disclosure.
3. Implement Today/navigation/composer, then progressive Patterns/Review disclosure.
4. Validate phone portrait/keyboard/safety/offline plus laptop and obtain review.
5. Only then resume additional synthetic-data work, as directed by the user.
