# M1 — Deterministic Safety Core

Status: COMPLETE / ACCEPTED. Historical milestone; criteria below were verified against `tests/test_milestone1.py` and the accepted implementation.

## Goal and state

Build deterministic safety policy before detectors, LLMs, UI, or wearables. `SafetyState` holds interaction mode, episode status, peak tier, explicit flags, dropout reason, degraded overlay/causes, sequence, and episode ID. Modes are T0 NORMAL, T1 CLARIFY, T2 ELEVATED, T3 URGENT, T4 IMMEDIATE; statuses are NONE, OPEN, RECHECK_REQUIRED, DROPOUT, CLOSED. FAIL_CLOSED is an overlay, not a tier.

## Invariants

Upgrades merge upward. Downgrades require named CAS-protected transitions using the current sequence; stale downgrades cannot erase newer evidence. Each mutation increases sequence under a single logical writer. Invalid states fail closed. Timers are explicit events, server time is authoritative, and tests inject a clock. Clinical policy parameters are external to transition code; no LLM controls policy.

## M1 acceptance gate

- **P1 — State-space validity:** produced states satisfy formal rules and invalid tuples fail closed (`tests/test_milestone1.py::test_p1_state_space_validity`).
- **P2 — Transition completeness:** every valid state/event pair has one deterministic result among TRANSITION, NO_STATE_CHANGE, REJECT_EVENT, SET_DEGRADED, DEFER_EVENT (`test_p2_transition_completeness`).
- **P3 — Tier monotonicity:** lowering the live tier requires an approved named transition and exact CAS sequence (`test_p3_tier_monotonicity`).

## Accepted M1 review corrections

The original M1 gate was re-run after review decisions. CLOSED + degraded is valid; `test_closed_failure_sets_overlay_and_preserves_episode` verifies fail-closed preservation. CLOSED episodes are immutable; `test_closed_new_evidence_creates_linked_episode` and `test_closed_recovery_evaluates_held_input_into_new_episode` verify a linked new episode after later concern. `CFG_URGENT_DEESCALATION_TARGET` and `CFG_IMMEDIATE_DEESCALATION_TARGET` have provisional T2 engineering defaults, not hard-coded clinical targets; `test_configured_high_tier_deescalations` verifies both CAS-protected edges.

## Stop condition

State types, validity checker, events, explicit transition dispatch, sequence/CAS, external configuration, and P1–P3 passed. No real detectors, LLM, wearable ingestion, or patient UI were included.
