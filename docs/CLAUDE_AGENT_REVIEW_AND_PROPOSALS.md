# aura-agent review, disclaimer consolidation, open input and agent feature proposals

2026-10-08. Claude (reviewer). **Recommendations only; not user-approved; no code changed.**
Static review of `aura_agent/*`, `aura_app/agent.py`, `aura_app/hosted.py`, `aura_ui/*`
and the framework §19. Verified: `tests.test_agent` 20 PASS (33 s). Not verified: live model
behaviour (I made no provider calls), UI in a browser, the other 175 tests.

User direction (2026-10-08): (1) too many disclaimers: remove them from the app and
summarize on one demo disclaimer page; (2) let users input information now; (3) use
aura-agent for human-readable data assessment; (4) recommend features that fully use the agent.

## 1. Review of the implementation

**What is good (keep):** no write tools exist; tool arguments are empty so the model cannot
choose a patient or inject parameters; source refs are hashed before the model sees them;
the guard fails closed on non-NORMAL safety modes, offline and invalid state; runs are
idempotent, race-checked (state fingerprint before and after generation) and traced;
stale cached runs are not replayed over new unsafe state; fallback is honestly labelled.

**Findings that matter for the new goals (most important first):**

1. **The lexical whitelist is what makes output unreadable.** `grounding.validate` rejects
   any claim containing a word that is not in the cited fact text or a ~400-word
   `CONNECTIVES` list (`UNSUPPORTED_FACTUAL_VOCABULARY`). A model cannot write natural
   prose under that rule, so output is stilted and often falls back (the handover reports
   vocabulary rejections). It is also not a semantic check: it can pass a sentence that
   reverses meaning using allowed words ("later" vs "earlier" are both allowed). The checks
   that carry the safety weight are the others: fact-ID citation, exact dates/numbers,
   signal and category match, prohibited-claims. Keep those; replace the vocabulary
   whitelist (see §4, change A).
2. **The "agent loop" is a fixed sequence, not agentic.** All six tools take zero arguments
   and return pre-built fact lists, so the model has no real choice; it calls them one at a
   time (parallel calls are rejected, `PARALLEL_TOOL_LIMIT`), which is why a run takes
   ~12 s. The same facts could be supplied in one prompt in ~3 s. Real tool use needs
   parameters (signal, date range, window comparison) with server-side bounds.
3. **Record Q&A is four canned questions** (`QUERIES`), and `_execute` rejects free text.
   For a user this is a menu, not an assistant.
4. **Disclaimers are baked into the fact text, so they leak into the agent's output and
   fallback.** `tools.py` writes sentences such as "Association does not establish
   causation", "Acknowledgement is not verified adherence", "Missing data is not a
   measurement", "Historical observation, not necessarily active now", "not sent and not
   patient-approved sharing". Those constraints belong in the system prompt and validator,
   and on the disclaimer page, not in the data the user reads.
5. **The held-input block is broader than it needs to be.** `_approval` sets `held` if any
   event in the patient's whole history is deferred or unassessed, and the guard then
   blocks every agent run for that patient. The clinician brief would disappear in the
   cases where it is most useful. Exclude held content from the prompt and keep blocking
   only on the safety mode (and show a static safety status instead).
6. **Model/config discrepancy to resolve.** The handover records OpenAI `gpt-6-luna`; you
   say DeepSeek flash is enabled. Only two of five roles have a live smoke result. Record
   the actual provider/model in the handover and run all five live once.

## 2. Disclaimer consolidation

Inventory (static count): ~25 disclaimer strings in `aura_ui/app.js`, 2 each in
`evidence.js` and `agent.js`, ~12 in `index.html` (demo panel, hosted notice, clinician
disclosure, "Prepared, not sent", "Not a clinical problem list", safety-evidence caption,
privacy notice, settings fine print), a long About page, plus the fact text above.

**Proposed rule: one source of truth, three things stay visible.**

| Keep in the app | Why |
|---|---|
| Pinned safety panel and resources (unchanged) | Mandatory safety output, never removed or generated (safety policy §35). |
| A single small "Demo" tag in the header that links to the Disclaimer page | Replaces every "synthetic" sentence. |
| A tiny "AI-written · sources" chip on each agent output | Honest disclosure of generated text; one word, not a sentence. |
| State chips that are functional, not disclaimers: "Not sent" on the visit draft, "Offline extraction" when no model ran | These report what happened. |

Everything else moves to a **Disclaimer page** (`#disclaimer`): what AURA is for (a demo
of a longitudinal companion for adults on stable antidepressant maintenance); that all
data is synthetic or user-entered demo data; that it is not a medical device, diagnosis,
treatment or emergency service; that AI drafts are checked against sources but not
clinically validated; safety resources are development content; sharing/clinician access
and authentication are not implemented; known limits. Optionally show it once on first visit
as a single dismissible card.

Constraints preserved without the text: the validator still blocks diagnosis, prediction,
treatment and causal claims; charts are labelled "Your own reference", not "normal range";
the "Not sent" chip stays because it states a fact.

## 3. Accepting user input now

Today the hosted demo accepts only labelled fixtures: `hosted.py` allows
`"fixture ordinary message"`, `"fixture safety concern"` and `"fixture review question"`,
and the safety gate is `DemoFixtureGate`, an allowlist. That is why input looks broken.
Two kinds of input have different safety needs:

**3a. Structured data, no free text (can be enabled first).**
- Enter a day's wearable values (sleep midpoint, duration, activity, resting HR),
  check-in, medication record. Validate ranges and types server-side, append to the user's
  private workspace, and let the existing longitudinal engine process them. Free text is
  absent, so the safety gate is not in play.
- **Import a wearable export** (CSV/JSON paste or upload). See feature F3: the agent maps
  columns, the user confirms, the server validates and imports deterministically.
- Caveat: baselines need history; a blank workspace will sit in building/provisional
  states. Offer "start from a seeded profile and add my days" or import ≥ several weeks.

**3b. Free-text notes and questions (needs a safety gate that does not exist yet).**
Framework §19 already permits what is needed: *"Detection must not rely on a single
model … semantic model detection"* are OR-combined detectors, *"Any detector may raise
concern. No model may lower concern."* Proposal for a `LayeredSafetyGate`:
1. Curated risk-phrase rules (deterministic).
2. Live-LLM semantic detector that can only **raise**: structured JSON
   `{concern: none|possible|likely}`.
3. Any `possible/likely` goes to the existing deterministic safety path (resources, tiers,
   structured follow-up). Timeout, invalid output or provider error **holds** the text
   (fail closed); it is stored but never sent to the agent.
4. Only text that passes both layers is stored as context and may reach the agent, quoted
   as data.
This keeps "models detect and explain, policy decides". It is a safety-policy-adjacent
decision and the detector is unvalidated; label it demo-only, test with an adversarial
set, and require user approval before Codex builds it. Until then free text stays held.

## 4. Human-readable assessment: what to change

- **A. Replace the lexical whitelist with claim-level verification.** Keep the numeric,
  date, signal, category, citation and prohibited-claim checks. Add (i) per-finding
  structured fields the model must fill (`signal`, `direction`, `since`, `fact_ids`) and a
  deterministic comparison with the engine's stored direction/dates, and (ii) an
  independent **verifier pass**, a second short model call that checks each claim is
  entailed by its cited facts and returns pass/fail per claim. Any fail drops that claim or
  falls back. This gives fluent prose with real grounding instead of a word list.
- **B. Clean the fact text** (remove embedded disclaimers; move rules to the prompt).
- **C. New output shape for "assessment":** headline (≤20 words); "What changed"
  (dated, with numbers); "Context recorded"; "Data gaps"; "Worth asking" (approved question
  intents only). Same output serves clinician and patient with different system prompts
  (clinical shorthand vs plain language).
- **D. Parametrized tools + parallel calls** (see F1) so the agent investigates rather than
  dumps; target <5 s.

## 5. Where the agent creates the most value (ranked)

Boundary for all: the engines decide what is true and safe; the agent reads, explains,
drafts, maps and proposes. No write tools; user-confirmed commands only.

1. **F1 Ask your record (free-form Q&A).** "Did my sleep change after the trip?" "Compare
   the last two weeks to the month before." Agent chooses among parametrized, bounded tools,
   including **deterministic analysis tools** computed server-side (window comparison
   median/spread, day-of-week pattern, gap summary) which return numbers with source IDs.
   The LLM decides what to call; it never computes. Patient version passes the safety gate.
2. **F2 Assessment on demand and after every input** (§4C), with chip "AI-written · sources".
   This is the clinician headline and the patient's "month at a glance".
3. **F3 Data intake agent.** Paste or upload any wearable export; the agent identifies the
   format, proposes column→signal mapping and unit/timezone handling, shows a preview, and
   the user confirms before a deterministic importer runs. Messy-format mapping is a task
   where an LLM is clearly better than rules and makes "input your data" practical.
4. **F4 Context elicitation.** After a drift, the agent picks the best approved clarifying
   question and turns the user's reply into a proposed context category + associated
   signal for the user to confirm. It proposes; it never clears a signal (framework §14/§28).
5. **F5 Raise-only semantic safety detector** (§3b). Highest stakes, strongest story:
   *AI raises, rules dispose.*
6. **F6 Visit pack.** One-page clinician brief + patient questions, printable/PDF, with
   sources; stays "Not sent" until a persisted approval workflow exists.
7. **F7 Persona-to-scenario for the demo.** "A 38-year-old shift worker who starts sleeping
   later…": the existing `aura_simulation/agent.py` planner (validated, offline today)
   turns it into a synthetic patient that the real engines then process. Judges can see the
   whole pipeline react to their own prompt. Offline template stays the fallback.
8. **F8 Verifier and red-team agents.** The verifier (§4A) is also reusable as an
   adversarial tester of the guard and detector for submission evidence.

## 6. Suggested order for the 2026-10-16 deadline (M8 window 13–15 Oct)

1. §4A+B+D and the F2 assessment (fixes readability, speed and the disclaimer leak).
2. Disclaimer page and removal of in-app disclaimers (low risk, user-visible immediately).
3. §3a structured input + F3 import.
4. F1 free-form Q&A with analysis tools.
5. Only with explicit approval: §3b/F5 gate for free text; then F4.
6. F7 if time remains.

## 7. Decisions needed from the user

1. Approve the disclaimer rule in §2 (keep safety panel, Demo tag, AI chip, state chips).
2. Approve replacing the lexical whitelist with claim verification + verifier pass.
3. Approve the raise-only LLM detector and free-text input (§3b), or keep free text held.
4. Confirm the active provider/model (DeepSeek flash vs `gpt-6-luna`) and allow a live
   sweep of all five roles.
5. Approve parametrized and deterministic analysis tools (an extension of the "no new
   statistics" stance: descriptive server-side tools, not engine decisions).
