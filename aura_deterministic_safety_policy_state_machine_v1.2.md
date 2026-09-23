# AURA Deterministic Safety Policy State Machine v1.2

**Status:** Implementation-ready safety-control specification, pending clinical review of tier criteria and patient-facing content  
**Parent framework:** AURA Health — Canonical Concept Framework v1.0  
**Supersedes:** AURA Deterministic Safety Policy State Machine v1.1  
**Target MVP population:** Adults aged 25–60 on stable clinician-managed antidepressant maintenance treatment  
**Scope:** Safety detection, deterministic transitions, fail-closed behavior, dropout/re-entry, re-checks, timers, output containment, auditability, and structural test requirements

> **Clinical boundary:** This document specifies software-control behavior. It does not claim that the tier criteria, suicide-risk instrument, patient wording, escalation resources, or follow-up timing are clinically validated. Those require qualified clinical review before real-world deployment.

---

## 1. Safety Doctrine

AURA may use probabilistic systems to help **notice** concern. Probabilistic systems do not control safety disposition.

> **Signals propose. Rules dispose. The LLM phrases.**

The machine follows these invariants:

> **Safety can move upward from new evidence. It may move downward only through an explicitly named deterministic policy edge.**

> **A safety-system failure may reduce functionality, but must never silently increase conversational freedom.**

> **The live safety floor comes from the current interaction mode. Episode peak tier records history and controls de-escalation/closure requirements; it is not the live floor.**

> **Upgrades merge. Downgrades compare-and-set.**

---

## 2. State Model

The active server-side safety state is:

```text
SafetyState = {
    interaction_mode,
    episode_status,
    episode_peak_tier,
    flags,
    dropout_reason,
    degraded,
    degraded_causes,
    sequence,
    episode_id
}
```

### Why the dimensions are separate

- `interaction_mode` governs what AURA may do **now**.
- `episode_status` governs the lifecycle of the safety episode.
- `episode_peak_tier` remembers the highest tier reached.
- `flags` stores policy-relevant facts required for deterministic replay.
- `dropout_reason` explains why an unresolved episode entered dropout.
- `degraded` is a fail-closed overlay, not a tier.
- `sequence` protects concurrent updates.
- `episode_id` scopes episode history and detector results.

---

## 3. Interaction Mode and Tier Mapping

| Tier | Interaction mode | Meaning |
|---|---|---|
| T0 | NORMAL | Ordinary AURA interaction |
| T1 | CLARIFY | Structured clarification required |
| T2 | ELEVATED | Meaningful concern requiring bounded support/follow-up |
| T3 | URGENT | Prompt human support required |
| T4 | IMMEDIATE | Immediate safety-oriented response required |

Tier and interaction mode are one-to-one in the MVP.

`FAIL_CLOSED` is not a mode and is not part of the ordering.

---

## 4. Episode Status

| Status | Meaning |
|---|---|
| NONE | No active safety episode |
| OPEN | Safety episode is active |
| RECHECK_REQUIRED | A mandatory post-high-tier re-check workflow remains outstanding |
| DROPOUT | Required high-tier or re-check interaction was not completed |
| CLOSED | Episode met closure requirements and awaits archival/reset |

---

## 5. Episode Peak Tier

`episode_peak_tier` is the maximum tier reached within the current episode.

Example:

```text
T0 -> T1 -> T2 -> T3 -> named de-escalation to T2
episode_peak_tier = T3
current tier       = T2
```

The peak tier does not block a named downgrade.

It controls:
- whether a mandatory re-check is required;
- dropout re-entry requirements;
- which closure rules apply;
- recent-high-tier history after archival.

Core rule:

> **Current mode controls the live floor. Peak tier controls what must happen before the episode can close.**

---

## 6. Policy Flags

Policy-relevant facts must be explicit state, not hidden annotations.

Each flag contains:

```text
PolicyFlag = {
    name,
    source_episode_id,
    set_at,
    expires_at | null,
    metadata
}
```

Initial v1.2 flag set:

```text
RECHECK_PASSED
T2_FOLLOWUP_INCOMPLETE
PRIOR_UNRESOLVED_HIGH_TIER
RECHECK_OVERDUE
REPEATED_ROUGH_CHECKINS
RECENT_SAFETY_DROPOUT
RAPID_PHQ_CHANGE
RECENT_HIGH_TIER_EPISODE
```

Rules:

- Episode-scoped flags are cleared when the episode is archived unless otherwise defined.
- Patient-level flags may survive archival with a policy-governed expiry.
- Flag lifetimes must be explicit.
- Replay uses the stored flags and their timestamps; no policy-relevant annotation may live only in prose or logs.

---

## 7. Dropout Reason

When `episode_status = DROPOUT`, `dropout_reason` is required.

Initial reasons:

```text
DURING_URGENT
DURING_IMMEDIATE
RECHECK_NOT_COMPLETED
```

`dropout_reason` is `null` for all non-DROPOUT statuses.

---

## 8. Degraded Overlay

`degraded = true` is a fail-closed overlay.

It does not overwrite:
- interaction mode;
- episode status;
- episode peak tier.

Example:

```text
interaction_mode   = URGENT
episode_status     = OPEN
episode_peak_tier  = T3
degraded           = true
degraded_causes    = { DETECTOR_TIMEOUT }
```

Recovery never restores a prior state because the prior state was never replaced.

---

## 9. Valid State Combinations

The transition engine must validate the tuple before every transition.

### Status = NONE

Valid only when:

```text
mode = NORMAL
peak = T0
episode_id = null
dropout_reason = null
```

Patient-level flags such as `RECENT_HIGH_TIER_EPISODE` may still exist.

### Status = OPEN

Valid when:

```text
mode ∈ {CLARIFY, ELEVATED, URGENT, IMMEDIATE}
peak >= mode tier
episode_id != null
dropout_reason = null
```

### Status = RECHECK_REQUIRED

Valid when:

```text
mode ∈ {NORMAL, CLARIFY, ELEVATED, URGENT, IMMEDIATE}
peak ∈ {T3, T4}
mode tier <= peak
episode_id != null
dropout_reason = null
```

This deliberately permits a returning dropout patient to re-enter a clinically configured re-check mode without creating an invalid tuple.

### Status = DROPOUT

Valid when:

```text
peak ∈ {T3, T4}
mode tier <= peak
episode_id != null
dropout_reason != null
```

Additional reason-specific rules:

- `DURING_URGENT` -> mode remains `URGENT`
- `DURING_IMMEDIATE` -> mode remains `IMMEDIATE`
- `RECHECK_NOT_COMPLETED` -> mode remains whatever valid mode was active in `RECHECK_REQUIRED` when the follow-up window expired

### Status = CLOSED

Valid when:

```text
mode = NORMAL
peak ∈ {T1, T2, T3, T4}
episode_id != null
dropout_reason = null
degraded = false
```

### Invalid examples

Invalid tuples include:

- `NORMAL + OPEN`
- `CLARIFY + NONE`
- `URGENT + OPEN + peak T2`
- `DROPOUT + peak T1`
- `DROPOUT + dropout_reason null`
- `CLOSED + ELEVATED`
- `peak < current mode tier`
- missing `episode_id` when status is not `NONE`
- non-null dropout reason outside `DROPOUT`
- unknown enum values

### Invalid-state behavior

Any invalid tuple results in:

```text
degraded = true
degraded_causes += { STATE_INTEGRITY_ERROR }
```

The system holds the current input, blocks ordinary chat, and does not guess the intended state.

---

## 10. Event Model

### Patient input

```text
FREE_TEXT_RECEIVED
STRUCTURED_RESPONSE_RECEIVED
CHECKIN_TAP_RECEIVED
MEDICATION_EVENT_RECEIVED
PATIENT_RETURNED
```

### Detector / system

```text
DETECTORS_COMPLETE
DETECTOR_TIMEOUT
DETECTOR_ERROR
POLICY_ERROR
STATE_INTEGRITY_ERROR
OUTPUT_VALIDATION_FAILED
CLIENT_RECONNECTED
LATE_DETECTOR_RESULT
```

### Clock

```text
RECONTACT_DUE
RECHECK_DUE
FOLLOWUP_WINDOW_EXPIRED
EPISODE_ARCHIVE_DUE
RESOURCE_REFRESH_DUE
FLAG_EXPIRY_DUE
```

### Resource

```text
LIVE_RESOURCES_AVAILABLE
LIVE_RESOURCES_UNAVAILABLE
RESOURCE_INTEGRITY_FAILED
```

### Named policy transitions

```text
CLARIFICATION_CLEARED
ELEVATION_RESOLVED
URGENT_DEESCALATION_APPROVED
IMMEDIATE_DEESCALATION_APPROVED
DROPOUT_REENTRY
RECHECK_PASSED
RECHECK_FAILED
EPISODE_CLOSE_APPROVED
```

Clock events are first-class machine inputs.

---

## 11. Authoritative Clock

Re-contact and re-check must not depend on the mobile app being open.

### Production

The **server clock/scheduler is authoritative** for:
- re-contact;
- re-check;
- follow-up expiry;
- flag expiry;
- episode archival;
- resource refresh.

### Test and simulation

The clock is injectable.

Example:

```text
clock.advance_to(t)
emit(RECHECK_DUE)
```

All timer events appear in the event log so replay is independent of wall-clock time.

---

## 12. Detector Architecture

### D1 — Structured deterministic triggers

Examples:
- safety-relevant validated-assessment responses;
- explicit structured declarations of intent, plan, or immediate danger.

### D2 — Curated phrase/rule detector

Deterministic recall floor for:
- direct self-harm language;
- direct suicidal language;
- indirect death-wish language;
- high-risk patterns requiring clarification.

### D3 — Dedicated semantic safety classifier

May propose:
- minimum tier;
- confidence;
- concern tags.

It may raise but never lower.

### D4 — Safety semantic model

May detect:
- euphemism;
- sarcasm;
- ambiguous intent;
- progressive disclosure;
- language missed by D2.

It may raise but never lower.

### D5 — Governed context flags

D5 consumes explicit policy flags and structured context.

It does not create an unbounded permanent floor.

Every D5 influence must define:
- activation condition;
- effect;
- expiry or clear condition.

### D6 — Passive / research-grade signals

Wearable and future E3 signals may justify:
- check-in;
- clarification;
- structured assessment.

D6 cannot independently establish T3 or T4.

---

## 13. Universal Safety Input Layer

Safety gating applies to all safety-relevant input, not only free text.

This includes:
- free text;
- PHQ responses;
- medication notes;
- side-effect notes;
- clinician-summary edits;
- structured safety answers;
- repeated `Rough` taps;
- other policy-designated structured events.

Repeated `Rough` check-ins may set a D5 flag even with no text.

---

## 14. Aggregation Rule

```text
proposed_tier = max(
    D1,
    D2,
    D3,
    D4,
    policy_map(D5)
)

effective_tier = max(
    current_interaction_tier,
    proposed_tier
)
```

D6 may trigger assessment/clarification but cannot independently propose T3/T4.

Peak update:

```text
new_peak = max(old_peak, new_interaction_tier)
```

The peak is never included in the live-floor `max()`.

---

## 15. Upgrade Merge Semantics

Upgrades may always merge upward within the current active episode.

```text
new_mode = max(current_mode, proposed_mode)
new_peak = max(current_peak, new_mode)
sequence = sequence + 1
```

A late detector result may raise the tier but cannot lower it.

---

## 16. De-escalation Compare-and-Set

Every downgrade carries:

```text
based_on_sequence
```

The transition commits only if:

```text
based_on_sequence == current.sequence
```

Otherwise:

```text
REJECT_EVENT
```

Example:

```text
seq 41 -> re-check proposes downgrade
seq 42 -> new concerning input raises to URGENT
late seq 41 downgrade -> rejected
```

Core rule:

> **Upgrades merge. Downgrades compare-and-set.**

This applies to:
- clarification clearance;
- T2 resolution;
- urgent de-escalation;
- immediate de-escalation;
- dropout re-entry if it lowers live tier;
- episode closure.

---

## 17. Single Writer and Sequence

Each active patient safety context has one logical state writer.

Requirements:
- detector jobs may run concurrently;
- state commits serialize per patient;
- each commit increments `sequence`;
- stale downgrades are rejected;
- stale closure attempts are rejected;
- upward evidence may still merge safely.

---

## 18. Policy Configuration Keys

Branch structure is deterministic now. Clinical reviewers may later change configuration values, not invent missing branches.

### CFG_T2_TIMEOUT_ACTION

Default:

```text
HOLD_ELEVATED_WITH_FLAG
```

On T2 `FOLLOWUP_WINDOW_EXPIRED`:
- remain `ELEVATED`;
- remain `OPEN`;
- set `T2_FOLLOWUP_INCOMPLETE`;
- no repeated re-contact beyond configured limit.

### CFG_RECHECK_FAILED_TARGET_BY_PEAK

Provisional conservative defaults:

```text
peak T3 -> target T3
peak T4 -> target T4
```

`RECHECK_FAILED` therefore returns the interaction mode to the episode peak tier unless a clinically approved configuration changes it.

### CFG_DROPOUT_REENTRY_TARGET_BY_PEAK

Provisional engineering defaults:

```text
peak T3 -> target T2
peak T4 -> target T3
```

`DROPOUT_REENTRY` always:
- uses compare-and-set;
- sets status to `RECHECK_REQUIRED`;
- clears `dropout_reason`;
- preserves peak.

These values require clinical review.

### CFG_RECENT_HIGH_TIER_TTL

Provisional engineering default:

```text
P7D
```

After archival of a T3/T4 episode:
- set `RECENT_HIGH_TIER_EPISODE`;
- retain source episode ID and prior peak;
- expire through `FLAG_EXPIRY_DUE`.

This value requires clinical review.

### CFG_MAX_RECONTACTS_PER_PHASE

Default:

```text
1
```

### CFG_BENIGN_CORPUS_FP_BUDGET

Prototype target:

```text
0.05
```

Not clinically validated.

---

## 19. NORMAL — T0

Allowed:
- ordinary AURA interaction;
- medication-routine support;
- contextual discussion;
- low-burden check-ins;
- clinician-preparation features.

Mandatory:
- all safety-relevant input enters the universal safety layer first.

Detector result T1–T4:
- create episode if none exists;
- status -> `OPEN`;
- mode -> proposed tier;
- peak -> proposed tier.

---

## 20. CLARIFY — T1

Purpose: obtain the minimum approved structured clarification.

Rules:
- ordinary open-ended coaching pauses;
- required policy questions cannot be bypassed by topic change.

### Named resolution

`CLARIFICATION_CLEARED` is a CAS downgrade.

Deterministic outcome:

```text
mode = NORMAL
status = CLOSED
```

The episode is never skipped directly to `NONE`.

Archival happens later via `EPISODE_ARCHIVE_DUE`.

---

## 21. ELEVATED — T2

Allowed:
- bounded supportive wording;
- appropriate human-contact suggestions under policy;
- clinician-summary preparation;
- scheduled follow-up.

Not allowed:
- therapy;
- treatment changes;
- “you are safe” conclusions;
- passive-data reassurance.

### ELEVATION_RESOLVED

Named CAS downgrade.

Outcome:

```text
mode = NORMAL
status = CLOSED
```

### T2 follow-up timeout

On `FOLLOWUP_WINDOW_EXPIRED`, apply `CFG_T2_TIMEOUT_ACTION`.

Default:

```text
mode = ELEVATED
status = OPEN
set flag T2_FOLLOWUP_INCOMPLETE
```

This is intentionally conservative until clinical review defines a different disposition.

The flag remains explicit state and is available to D5 and clinician review.

---

## 22. URGENT — T3

Required:
- stop ordinary coaching;
- pin reviewed human-support resources outside LLM text;
- ask only policy-defined questions.

### Output rule

LLM phrasing may be used only if deterministic validation confirms:
- required elements are present;
- urgency is not softened;
- prohibited reassurance is absent;
- unsupported treatment instructions are absent.

Validation failure -> static approved fallback template.

### Named de-escalation

`URGENT_DEESCALATION_APPROVED`:
- CAS required;
- target mode is set by clinical policy;
- status -> `RECHECK_REQUIRED`;
- peak remains unchanged.

No direct transition to CLOSED.

---

## 23. IMMEDIATE — T4

Uses fixed, pre-approved text only.

No generative phrasing.

Required:
- native pinned safety resources;
- concise immediate-safety template;
- only policy-defined structured questions.

### Named de-escalation

`IMMEDIATE_DEESCALATION_APPROVED`:
- CAS required;
- target mode set by clinical policy;
- status -> `RECHECK_REQUIRED`;
- peak remains T4.

No direct transition to CLOSED.

---

## 24. Degraded / Fail-Closed Behavior

### Server-side degraded overlay

Set `degraded=true` when a safety-critical component cannot safely complete.

Examples:
- detector timeout/error;
- policy-engine error;
- invalid state;
- output-validation infrastructure failure with no safe static fallback;
- trusted-resource integrity failure.

### While degraded

If the deterministic transition engine is still healthy:

- status-only clock transitions that do not depend on failed probabilistic components may still execute;
- D1 structured deterministic triggers may still raise tier;
- upward deterministic evidence may still merge;
- ordinary LLM conversation remains blocked for held input.

If the policy engine or state-integrity layer itself is degraded:

- no safety-state mutation occurs except recovery/repair bookkeeping;
- incoming events are logged/deferred;
- the UI remains fail closed.

The cause set in `degraded_causes` determines which deterministic operations remain safe.

### Recovery

- re-evaluate held input;
- merge only upward from preserved mode;
- clear only the recovered causes;
- never downgrade as a recovery side effect.

---

## 25. Client-Side Offline Fail-Closed Path

Loss of device connectivity is separate from server-side degraded state because the server may not know the client is offline.

When the client cannot reach the safety service:

- hold the patient input locally in protected storage;
- do not send it to any remote or local conversational LLM;
- display the built-in last-known-good safety resource bundle;
- state that AURA cannot safely process the message while offline;
- preserve the original input ID and timestamp.

On reconnect:

```text
emit(CLIENT_RECONNECTED)
submit held input with original input_id/timestamp
```

The server evaluates it normally.

The client must not tell the patient that the held input was assessed before server evaluation actually occurs.

---

## 26. Safety Resource Bundle

AURA maintains:

### Live registry
Server-maintained and versioned.

### Built-in last-known-good bundle
Shipped with the application and updated through verified releases.

Bundle fields:
- resource ID;
- label;
- contact method;
- locale;
- last-verified timestamp;
- version;
- integrity signature/hash.

If live resources are unavailable:
- use built-in bundle.

If the built-in bundle is stale:
- **still display it**;
- add a clear staleness note;
- never hide it solely because it is old.

Safety resources are native UI components and are never generated by the LLM.

---

## 27. RECHECK_REQUIRED

Used whenever a T3/T4 episode still requires a post-acute structured re-check.

Valid mode may be T0–T4 as long as:
- peak is T3/T4;
- mode <= peak.

### RECHECK_DUE

Request the approved re-check.

### RECHECK_PASSED

Deterministic action:
- set `RECHECK_PASSED`;
- do not close automatically.

### EPISODE_CLOSE_APPROVED

Valid only if:
- `RECHECK_PASSED` is present when peak is T3/T4;
- no unresolved higher detector result exists;
- CAS sequence matches.

Outcome:

```text
mode = NORMAL
status = CLOSED
```

If requirements are missing:

```text
REJECT_EVENT
```

### RECHECK_FAILED

Target mode comes from `CFG_RECHECK_FAILED_TARGET_BY_PEAK`.

Default:
- peak T3 -> URGENT
- peak T4 -> IMMEDIATE

Status returns to `OPEN`.

Clear `RECHECK_PASSED` if present.

---

## 28. DROPOUT

Used for unresolved high-tier or mandatory re-check workflows.

### Entering dropout

#### URGENT timeout

```text
mode = URGENT
status = DROPOUT
peak >= T3
dropout_reason = DURING_URGENT
```

#### IMMEDIATE timeout

```text
mode = IMMEDIATE
status = DROPOUT
peak = T4
dropout_reason = DURING_IMMEDIATE
```

#### Re-check timeout

Preserve the current valid re-check mode:

```text
mode = current mode
status = DROPOUT
dropout_reason = RECHECK_NOT_COMPLETED
peak unchanged
```

### Patient returns

`PATIENT_RETURNED` does not directly mutate the tier.

It causes the policy engine to propose the named CAS edge:

```text
DROPOUT_REENTRY
```

`DROPOUT_REENTRY`:
- requires current sequence match;
- status -> `RECHECK_REQUIRED`;
- target mode -> `CFG_DROPOUT_REENTRY_TARGET_BY_PEAK`;
- clears `dropout_reason`;
- preserves peak;
- does not close episode.

Thus no unnamed downgrade exists.

---

## 29. CLOSED and Archival

`CLOSED` means deterministic closure conditions have been met.

### EPISODE_ARCHIVE_DUE

On archival:
- preserve complete episode record;
- if peak T3/T4, set patient-level `RECENT_HIGH_TIER_EPISODE`;
- set flag expiry from `CFG_RECENT_HIGH_TIER_TTL`;
- active state becomes:

```text
mode = NORMAL
status = NONE
peak = T0
episode_id = null
```

Episode-scoped flags are cleared.

Patient-level flags remain until their own expiry events.

---

## 30. Late Detector Results Across Episode Boundaries

Every detector result includes:

```text
input_id
source_episode_id
source_sequence
detector_id
proposed_tier
```

If a detector result arrives after its source episode was archived:

1. log the result against the **original source episode ID**;
2. do not rewrite the archived episode;
3. if proposed tier is T0 -> no live state change;
4. if proposed tier is T1–T4:
   - if a current episode exists, merge upward into the current episode;
   - if no current episode exists, create a **new linked episode**;
5. record:

```text
triggered_by_late_result_from_episode_id = source_episode_id
```

This preserves conservative safety behavior without corrupting episode history.

---

## 31. Core Transition Table

The implementation stores transitions as data.

| Current condition | Event | Deterministic outcome |
|---|---|---|
| invalid tuple | any | set degraded / state-integrity failure |
| any healthy state | DETECTOR_TIMEOUT / DETECTOR_ERROR | set degraded cause; preserve mode/status/peak |
| degraded, detector cause only | D1 higher structured trigger | upward merge allowed |
| degraded, policy/state-integrity cause | any state-changing event | defer/log; no state mutation |
| NORMAL/NONE | proposed T1–T4 | create OPEN episode, set mode and peak |
| CLARIFY/OPEN | CLARIFICATION_CLEARED | CAS -> NORMAL/CLOSED |
| CLARIFY/OPEN | proposed higher tier | upward merge |
| ELEVATED/OPEN | ELEVATION_RESOLVED | CAS -> NORMAL/CLOSED |
| ELEVATED/OPEN | proposed T3/T4 | upward merge |
| ELEVATED/OPEN | RECONTACT_DUE | one bounded re-contact if allowed |
| ELEVATED/OPEN | FOLLOWUP_WINDOW_EXPIRED | apply CFG_T2_TIMEOUT_ACTION |
| URGENT/OPEN | URGENT_DEESCALATION_APPROVED | CAS -> configured lower mode + RECHECK_REQUIRED |
| IMMEDIATE/OPEN | IMMEDIATE_DEESCALATION_APPROVED | CAS -> configured lower mode + RECHECK_REQUIRED |
| URGENT/OPEN | FOLLOWUP_WINDOW_EXPIRED | DROPOUT / DURING_URGENT |
| IMMEDIATE/OPEN | FOLLOWUP_WINDOW_EXPIRED | DROPOUT / DURING_IMMEDIATE |
| RECHECK_REQUIRED | RECHECK_DUE | request re-check; no automatic tier change |
| RECHECK_REQUIRED | RECHECK_PASSED | set RECHECK_PASSED flag |
| RECHECK_REQUIRED | EPISODE_CLOSE_APPROVED | CAS -> NORMAL/CLOSED if closure preconditions hold |
| RECHECK_REQUIRED | RECHECK_FAILED | apply configured target, status OPEN |
| RECHECK_REQUIRED | FOLLOWUP_WINDOW_EXPIRED | DROPOUT / RECHECK_NOT_COMPLETED, preserve mode |
| DROPOUT | PATIENT_RETURNED | propose DROPOUT_REENTRY |
| DROPOUT | DROPOUT_REENTRY | CAS -> RECHECK_REQUIRED + configured target mode |
| CLOSED | EPISODE_ARCHIVE_DUE | archive; NORMAL/NONE/T0; maybe set RECENT_HIGH_TIER_EPISODE |
| any state | FLAG_EXPIRY_DUE | clear matching expired flag |
| any healthy state | higher new detector result | upward merge |
| any state | stale downgrade / stale closure | REJECT_EVENT |
| archived source episode | LATE_DETECTOR_RESULT T1–T4 | log on old episode; merge into current or create linked new episode |

---

## 32. Policy-Table Completeness Rule

The full implementation table must define exactly one result for every:

```text
(valid SafetyState, accepted Event)
```

Allowed result classes:

```text
TRANSITION
NO_STATE_CHANGE
REJECT_EVENT
SET_DEGRADED
DEFER_EVENT
```

No pair may be undefined.

Irrelevant events must still resolve explicitly to either:
- `NO_STATE_CHANGE`, or
- `REJECT_EVENT`.

Invalid state tuples always resolve to:

```text
SET_DEGRADED
```

---

## 33. Degraded + Clock Event Rules

Timers continue to fire at the authoritative server even while degraded.

### If transition engine is healthy

The following may still execute because they do not require probabilistic detector output:

- `FOLLOWUP_WINDOW_EXPIRED`;
- `RECHECK_DUE`;
- `FLAG_EXPIRY_DUE`;
- `EPISODE_ARCHIVE_DUE`, if all archival preconditions were already satisfied.

A timer may change status or flags while preserving the current mode floor.

### If policy/state integrity is degraded

Timer events are:
- logged;
- marked deferred;
- replayed after recovery in timestamp order.

They do not mutate safety state while the transition engine itself is untrusted.

This behavior must be replay-tested.

---

## 34. Determinism Boundary

AURA does not claim D3/D4 model outputs are deterministic.

AURA claims:

> **Given identical prior state, explicit flags, detector outputs, structured answers, policy configuration, resource version, and clock events, the transition engine produces the same resulting state and action set.**

Replay must reproduce the same transitions exactly.

---

## 35. LLM Output Containment

### NORMAL
Ordinary bounded AURA generation allowed.

### CLARIFY
Only policy-defined question content may be phrased.

### ELEVATED
Constrained support generation allowed.

### URGENT
Generated phrasing allowed only after deterministic output validation.

Validation failure -> static approved fallback template.

### IMMEDIATE
No LLM.

Fixed approved template only.

### degraded
No LLM.

Static fail-closed UI only.

### client offline
No LLM.

Static offline fail-closed UI only.

### Safety resources
Native/pinned UI outside generated text.

---

## 36. Evaluation Corpora

Three corpora are required.

### A. Risk corpus

Includes:
- explicit suicidal language;
- indirect death wishes;
- burden language;
- hopelessness;
- preparatory language;
- plan/intent statements;
- progressive disclosure;
- slang and misspellings.

### B. Ambiguous / third-party corpus

Includes:
- “My friend said she wants to die.”
- possible third-person disclosure;
- third-party concern;
- ambiguous quotations;
- statements that may be distancing language for self-disclosure.

Entering `CLARIFY` for appropriate examples is **not** counted as a benign false positive.

This corpus is reported separately.

### C. Benign / figurative corpus

Includes:
- “This deadline is killing me.”
- “I’ll die if I have another meeting.”
- “My boss is driving me insane.”
- ordinary idioms;
- jokes;
- clearly fictional/media quotations;
- clearly non-self-referential figurative speech;
- routine frustration.

Third-party safety statements are **not** placed in this corpus.

---

## 37. Provisional False-Positive Budget

For hackathon/demo engineering evaluation:

> **No more than 5% of benign-corpus inputs may enter CLARIFY or higher, and 0% may enter URGENT or IMMEDIATE.**

This is a provisional prototype target, not a clinically validated threshold.

Every safety evaluation report must show together:

- risk-corpus recall;
- benign-corpus false-positive rate;
- ambiguous-corpus disposition;
- confusion by tier;
- unnecessary clarifications;
- missed high-risk examples.

AURA must not optimize recall without measuring the burden created by false alarms.

---

## 38. Structural Property Tests

These run before detector tuning or clinical-content work.

### P1 — State-space validity

Every stored tuple must satisfy Section 9.

Invalid state -> degraded.

### P2 — Transition completeness

Every valid `(state, event)` pair has exactly one result.

### P3 — Tier monotonicity

Live tier never decreases except through a named CAS downgrade.

### P4 — Peak monotonicity

Peak never decreases inside an episode.

### P5 — Replay determinism

Same:
- state;
- flags;
- detector outputs;
- structured answers;
- policy config;
- resource version;
- clock events

must produce the same transitions.

### P6 — Stale downgrade rejection

Old sequence -> downgrade rejected.

### P7 — Upward race safety

Late detector evidence can raise but never lower.

### P8 — Fail-closed preservation

Setting degraded does not overwrite mode/status/peak.

### P9 — Resource fallback

Live registry failure yields built-in resources.

Stale built-in resources remain visible with a staleness note.

### P10 — LLM containment

No generated text in IMMEDIATE, degraded, or client-offline fail-closed paths.

### P11 — Pinned resource independence

LLM output cannot remove resource UI.

### P12 — Dropout validity

All three dropout reasons generate valid tuples.

### P13 — Dropout re-entry

Re-entry uses named CAS `DROPOUT_REENTRY`, never direct NORMAL.

### P14 — Recheck closure state visibility

`RECHECK_PASSED` must be stored explicitly before closure can succeed.

### P15 — T2 incomplete visibility

`T2_FOLLOWUP_INCOMPLETE` must be explicit and replay-visible.

### P16 — Cross-episode stale result

Late detector evidence is logged on the original episode and cannot rewrite it.

### P17 — Client-offline containment

Offline input never reaches an LLM before server safety evaluation.

### P18 — Recent high-tier memory

Archiving T3/T4 sets `RECENT_HIGH_TIER_EPISODE`; expiry occurs only through the configured clock event.

---

## 39. Audit Record

Every committed transition records:

- pseudonymous patient/session identifier;
- episode ID;
- linked source episode ID where applicable;
- prior state tuple;
- explicit flags;
- event;
- detector outputs;
- proposed tier;
- resulting state tuple;
- sequence;
- policy version;
- policy configuration version;
- resource-bundle version;
- clock-event timestamp;
- upgrade vs. named downgrade;
- CAS base sequence;
- LLM/static-template use;
- output-validation result;
- re-contact count;
- dropout reason;
- closure reason;
- degraded causes;
- deferred-event status.

Sensitive free text should not be duplicated unnecessarily where structured references suffice.

---

## 40. Policy Versioning

Safety policy is versioned independently of the conversational model.

A release records:

- policy version;
- effective date;
- transition-table checksum;
- state-schema version;
- detector-interface version;
- policy-flag definitions;
- policy-configuration values;
- timer configuration;
- resource-bundle minimum version;
- static-template versions;
- test-suite version;
- clinical-review status;
- known limitations.

Changing the LLM does not change the transition policy.

---

## 41. Minimum MVP Acceptance Criteria

The engine is not demo-ready until:

1. All safety-relevant text and structured inputs enter the safety layer.
2. D1–D5 inputs are observable in logs.
3. Upward merges cannot be overridden by lower evidence.
4. Peak tier does not act as the live floor.
5. Every downgrade uses a named CAS edge.
6. All dropout reasons produce valid tuples.
7. `DROPOUT_REENTRY` is named, CAS-protected, and transitions to `RECHECK_REQUIRED`.
8. `CLARIFICATION_CLEARED` deterministically closes to NORMAL/CLOSED.
9. `ELEVATION_RESOLVED` deterministically closes to NORMAL/CLOSED.
10. T2 timeout has the configured deterministic default.
11. `RECHECK_FAILED` has a configured deterministic target.
12. `RECHECK_PASSED` is explicit replay-visible state.
13. `T2_FOLLOWUP_INCOMPLETE` is explicit replay-visible state.
14. `RECHECK_REQUIRED + EPISODE_CLOSE_APPROVED` is explicitly implemented.
15. Server degraded and client-offline fail-closed paths both work.
16. Clock events have defined degraded behavior.
17. Live-resource failure falls back to built-in resources.
18. Stale fallback resources remain visible with a staleness note.
19. IMMEDIATE uses fixed approved text only.
20. URGENT output is validated or replaced by static fallback.
21. No LLM is used while degraded or client-offline.
22. Safety resources are outside LLM text.
23. P1 state validity passes.
24. P2 transition completeness passes.
25. P3 monotonicity passes.
26. P5 replay determinism passes.
27. Cross-episode late detector handling passes.
28. Benign false-positive rate and risk recall are reported together.
29. Third-party/ambiguous statements are evaluated separately.
30. The UI clearly says AURA is not an emergency monitoring service.

---

## 42. Notes for Clinical Reviewers

Please approve or revise:

- mapping of evidence to T1–T4;
- structured clarification questions;
- use of C-SSRS or another validated instrument;
- URGENT vs. IMMEDIATE criteria;
- T2 timeout disposition;
- `CFG_DROPOUT_REENTRY_TARGET_BY_PEAK`;
- `CFG_RECHECK_FAILED_TARGET_BY_PEAK`;
- `CFG_RECENT_HIGH_TIER_TTL`;
- re-contact timing;
- re-check timing;
- fixed patient-facing templates;
- Singapore safety-resource ordering;
- which safety events belong in clinician summaries.

The engineering defaults are placeholders to make branch structure testable, not clinical recommendations.

---

## 43. Notes for Technical Reviewers

Please challenge:

- tuple validity constraints;
- flag lifetimes;
- transition completeness;
- sequence-number/CAS design;
- single-writer semantics;
- durable timers;
- degraded capability rules;
- event deferral and replay;
- client-offline storage and resubmission;
- detector idempotency;
- late cross-episode results;
- state-integrity checks;
- resource signature verification;
- audit-log integrity.

Critical question:

> **Can any race, timeout, offline period, restart, stale result, or stale downgrade make the safety state less restrictive than deterministic policy permits?**

Required answer: **no**.

---

## 44. Notes for Product / Human-Factors Reviewers

Please assess:

- CLARIFY frequency;
- idiom false positives;
- ambiguous third-party handling;
- whether wording feels coercive;
- whether repeated safety flows encourage under-reporting;
- whether T2 timeout behavior is too restrictive;
- dropout messaging;
- pinned-resource burden;
- re-check burden;
- offline fail-closed messaging;
- whether stale-resource notices are understandable.

The safety system must protect against both:
- missed risk;
- over-escalation that destroys trust.

---

## 45. Notes for Regulatory / Governance Reviewers

Please verify:

- intended-use implications of deterministic safety handling;
- whether any output drives clinical management;
- storage of unresolved safety episodes;
- retention/audit duties;
- handling of unreachable users;
- resource-registry operational responsibilities;
- cross-device/server safety state synchronization;
- whether UI claims exceed the prototype intended use.

This specification does not assign AURA an HSA device class.

---

## 46. Open Clinical Parameters

The machine structure is now implementation-ready, but these remain pending clinical review:

- exact tier criteria;
- structured safety instrument;
- D2 phrase corpus;
- D3/D4 model choice;
- D5 policy mappings;
- T2 follow-up window;
- T3/T4 re-contact interval;
- re-check interval;
- urgent/immediate de-escalation target modes;
- live resource contents;
- resource freshness threshold;
- final false-positive budget;
- clinically acceptable recall;
- patient-facing wording.

---

## 47. Final Safety Contract

> **The live floor comes from the current interaction mode. Peak tier records history and governs closure requirements.**

> **Policy-relevant facts are explicit state, not hidden annotations.**

> **Upgrades merge. Downgrades compare-and-set.**

> **FAIL_CLOSED is an overlay, not a tier.**

> **Dropout has an explicit reason, and re-entry is a named deterministic edge.**

> **Every valid state/event pair has exactly one result. Invalid states fail closed.**

> **Timers are explicit events from an authoritative server clock and an injectable test clock.**

> **Offline clients fail closed locally.**

> **Stale detector results preserve their original episode provenance.**

> **Safety resources remain visible even when the live registry is unavailable or the fallback bundle is stale.**

> **The LLM never owns emergency resources, IMMEDIATE wording, or policy transitions.**

> **AURA measures both missed risk and false alarms.**

> **AURA supports human care; it does not replace it.**
