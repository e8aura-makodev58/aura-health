# M3 — Longitudinal Context Engine

Status: COMPLETE / ACCEPTED. Canonical acceptance evidence: [`MILESTONE3_REVIEW.md`](../../MILESTONE3_REVIEW.md). L1–L14 were verified against that review and the repository tests.

## Goal and domain

Answer “What changed from this patient's usual pattern?”—not “Is this patient becoming depressed?” Domain concepts cover sleep, activity, resting heart rate, medication events, check-ins, context, sensing, baseline trust, anchors, rolling baseline, drift, held-for-review, and communication.

Sensing (`OBSERVED`/`UNOBSERVED`) and trust (`PROVISIONAL`/`TRUSTED`/`REESTABLISHING`) are orthogonal. Anchored and rolling references are separate; only governed commands move an anchor. Communication includes STAY_QUIET, MICRO_CHECKIN, TARGETED_CLARIFICATION, STRUCTURED_ASSESSMENT, CLINICIAN_REVIEW_ITEM, and safety handoff. Longitudinal logic never assigns T1–T4.

## Accepted structural properties

- **L1:** anchor moves only on a permitted explicit event.
- **L2:** rolling reference updates without moving anchor.
- **L3:** missingness never becomes zero, healthy, or pathological.
- **L4:** sensing and baseline trust are independent.
- **L5:** rolling-vs-anchor reveals slow persistent drift.
- **L6:** benign context attenuates only associated signals.
- **L7:** benign context cannot clear unrelated subjective evidence.
- **L8:** `EXPLAINED_HELD_FOR_REVIEW` does not move anchor.
- **L9:** held drift suppresses duplicate notifications.
- **L10:** relevant new evidence reopens held drift.
- **L11:** wearable return after a long gap enters REESTABLISHING.
- **L12:** STAY_QUIET is a valid decision.
- **L13:** safety decisions delegate to `aura_safety`.
- **L14:** identical synthetic seed/config/timeline/events replay deterministically.

## Scenarios and evaluation

- **A — physical illness:** physiology changes with illness and stable self-report; avoid unsupported mental-health conclusions and unnecessary burden.
- **B — slow drift:** rolling adapts, while rolling-vs-anchor exposes accumulated change.
- **C — illness plus independent change:** illness attenuates linked physiology, not unrelated evidence.
- **D — explained benign persistent change:** anchor unchanged, held-for-review entered, duplicates suppressed, review item retained.
- **E — wearable gap:** absence is not pathology; return is OBSERVED + REESTABLISHING, not automatically fully trusted.

Fixed-threshold and rolling-only comparators illustrate engineering behavior, not clinical efficacy. M3 stopped when L1–L14, Cases A–E, comparator metrics, and replay passed, with latent simulator truth outside production decisions.
