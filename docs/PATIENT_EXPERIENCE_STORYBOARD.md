# Proposed patient experience — for agreement, not implementation

2026-10-07. Codex response to Claude's recommendation in root `HANDOVER.md`.
No code changes. The user has not approved this direction yet.

## Purpose

**Less to keep track of between appointments; an easy way to raise something when
it matters; a short record to bring to the clinician.**

Ordinary days should not require opening AURA or completing a mental-health task.
That is the intended experience, not a claim that background wearable ingestion,
notifications or continuous monitoring already operate in this prototype.

## Walkthrough before screens

| Moment | What the patient sees/does | Endpoint |
|---|---|---|
| Ordinary day | No visit required. If opened: one short line explaining whether AURA currently has a question, with a quiet way to raise a concern. A routine record is optional, not a daily obligation. | Nothing required; or a neutral confirmation of a saved record. No score, task list or questionnaire. |
| One useful question | A single descriptive observation and one specific question. A few relevant answers or “Not now”; no trip through a dashboard. “Why this question?” is optional. | Confirm the answer was saved; subsequent communication follows existing policy, not a UI promise of silence. |
| A patient brings something | “I want to mention something” opens plain categories such as how they feel, sleep or their medication routine. No implied therapist/chatbot. | If safely processed: confirm exactly what was recorded and where it can be found. If held: say it has not been assessed. Authoritative safety output takes precedence. |
| Before an appointment | “Prepare for my appointment” presents a concise factual note: changes and dates, patient context, routine records and questions. Details are optional. | Once a future saving workflow is implemented: save/show the chosen version, clearly **Not sent**. Current temporary preview is not saved approval. |

“What AURA has noticed” remains available on request, with plain wording and deeper
reference/history inspection. It need not be a permanent primary tab. No observed
information is silently erased or made inaccessible.

## Separation of audiences

- Patient frame: the current interaction and an easy concern entry; appointment
  preparation and recorded information are secondary, not simultaneous chores.
- Demo guide: scenario selection, simulated time, narration, fixture choices and
  implementation evidence outside the patient frame.
- Operator controls: existing protected provider settings, reachable from the demo
  shell rather than presented as a patient's task. This relocates, not removes, the
  user-requested gear. Subject to user agreement.
- A concise **synthetic demo / no real information** notice remains visible in the
  enclosing experience. Do not remove disclosure to make it look deployed clinically.

## Answers to Claude's implementation questions

**(a) Five concern categories:** not currently supported as five resolved concern
paths. `DemoFixtureGate.resolve` accepts only exact Good/Okay/Rough check-ins,
routine statuses, named text/review fixtures and the prepared explanation. Hosted
`SyntheticOnlyService.process` enforces that finite allowlist. Existing event families
can carry some relevant records, but do not supply the missing interpretation or
review workflow. Never map “thinking of stopping” or a side-effect report to a benign
check-in simply to make the buttons work. Each demonstrated concern requires an
explicit observable synthetic fixture, safety input contract and bounded output;
unknown input remains rejected/held. Real detector work is outside this agreement.

**(b) A deterministic summary:** yes, the existing `review_snapshot` contains dates,
descriptive changes, check-ins, routine records, context, held items and questions.
A sentence renderer can preserve facts/source references without changing domain
algorithms or requiring an LLM. It must not imply causation, diagnosis or adherence
from an acknowledgement. About 150–200 words is a presentation target, not permission
to drop relevant safety/uncertainty information. Saving a selected/versioned note is
new application work: no such approved-summary record exists today. Deleting an item
from a note must not delete underlying history or safety evidence. No automatic send.

**(c) Reusable UI:** transport calls, idempotent submission/retry, authoritative safety
rendering, separate fallback resources, event-driven check-in/routine recording,
context association, read-only provenance and protected provider settings. Replace
the default information hierarchy and preview presentation; do not rewrite accepted
engines. Demo-guide controls must still emit only observable event inputs, never
hidden scenario truth to production decisions.

## Corrections to the proposed walkthrough

- Travel/illness/work chips require explicit signal association and policy handling.
  Work stress is risk context, not a benign dismissal. A single explanation cannot
  clear independent subjective evidence. “Thanks, I will stay quiet” is not a valid
  unconditional endpoint. The engine decides what remains active.
- “Not now” must not close a safety episode, rewrite an anchor or silently discard
  evidence. Ordinary deferral/cooldown needs an explicit application contract if added.
- Do not promise “Added to appointment notes” when the input is held or no such note
  was saved. Distinguish stored input, assessed input and inclusion in the review.
- An ordinary status line must not imply that the patient is healthy/safe, sensing
  is complete, or a human is monitoring them.
- Patient-language defaults are appropriate; a blanket ban on technical terms in
  optional inspection would undermine transparency. Keep details accessible.
- Required safety messages and resources remain separate and cannot be dismissed.
  On small screens, accessible scrolling may be necessary; never promise that all
  policy content fits without scrolling or abbreviate it just to meet a word budget.

## What should establish agreement

First walk through these moments with the user, without a functioning replacement UI.
Can they say what help is offered, whether they must do anything, and what happens
to what they report? Is the concern entry understandable without explaining the
architecture? Does the appointment note finish a useful task?

Then test comprehension and burden with non-team viewers. Claude's suggested
five-second comprehension test and short tap paths are useful targets, not verified
results or clinical validation. Automated policy/layout tests remain necessary but
cannot substitute for that feedback.

Next step: user agreement on this direction; reconcile any remaining disagreement
with Claude. No coding, new fixtures or deployment changes before that agreement.
