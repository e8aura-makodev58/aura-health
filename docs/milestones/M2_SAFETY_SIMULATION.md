# M2 — Safety Structural Properties and Simulator

Status: COMPLETE / ACCEPTED. Historical milestone; IDs below were verified against `tests/test_milestone2.py`.

## Goal

Complete safety-machine structural properties and deterministic simulation/replay before real detectors or an LLM. M1 review corrections—CLOSED + degraded, immutable post-CLOSED handling, and configured CAS-protected high-tier de-escalation—remained authoritative in M2; they were **not first decided in M2**.

## Structural properties

- **P4 — Peak monotonicity:** an episode's peak never decreases.
- **P5 — Replay determinism:** fixed initial state, resolved inputs, flags, configuration, clock events, and resource version reproduce states/actions.
- **P6 — Stale downgrade rejection:** an old sequence cannot downgrade newer state.
- **P7 — Upward race safety:** newer/upward evidence is not lost to stale lower-tier operations.
- **P8 — Fail-closed preservation:** degradation preserves live mode, status, and peak.
- **P9 — Resource fallback:** live lookup failure retains last-known-good safety resources.
- **P10 — LLM containment:** prohibited modes do not depend on generation.
- **P11 — Pinned-resource independence:** critical resource display does not depend on generated text.
- **P12 — Dropout validity:** reason-specific dropout states retain valid peak history.
- **P13 — Dropout re-entry:** patient return uses named CAS-protected `DROPOUT_REENTRY`.
- **P14 — Recheck closure-state visibility:** recheck completion is explicit state, not transient annotation.
- **P15 — T2 incomplete-state visibility:** incomplete elevated follow-up is explicit/replayable.
- **P16 — Cross-episode stale detector handling:** late results retain provenance and cannot rewrite archived episodes.
- **P17 — Client-offline containment:** local offline fail-closed behavior invokes no LLM.
- **P18 — Recent high-tier memory:** governed high-tier history remains available after closure/archival.

## Simulator and stop condition

The developer simulator exercises resolved detector proposals, structured answers, clock events, races/stale downgrades, T2 timeout, high-tier de-escalation, dropout/re-entry, recheck, detector failure, degradation, offline containment, and CLOSED-to-new-episode behavior through the production transition engine. M2 stopped when P1–P18, simulation, and exact saved-trace replay passed, with no undefined valid pair and no real detector, patient UI, or LLM.
