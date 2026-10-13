# Review of Claude's Q&A fixes and patient loading animation

2026-10-13 — Codex Sol. Reviewed `c9922cd` against `74731e6`.
Review only: no runtime edits, paid model calls, quota changes or deployment.

## Assessment

Claude's changes are directionally correct and appropriately scoped to the
bugs-only freeze. Clinician questions no longer become patient reports on the
explicit clinician path. Patient questions retain their existing safety-first
processing. Actor choice participates in request identity; source guards,
idempotent replay and independent verification remain in place.

The fallback is improved: status lines are removed from free-question selection,
and "Related facts from the record" does not falsely claim a checked answer.
Sanitized provider failure labels now distinguish demo budget, disabled and
unconfigured states. Limits were not increased. Prompt version is now v11.

The actor distinction is adequate for this synthetic demo, not production
authorization. `asker` is client-supplied; regex refusal is not an authenticated
role check or a complete classifier of patient testimony. Keep this limitation
explicit. Clinician questions quoting curated safety phrases are also refused;
that is a conservative demo restriction, not a clinically complete Q&A workflow.

## Findings and recommended improvements

### 1. Preserve exact facts in clinician Q&A — medium

`aura_ui/agent.js:165` routes Q&A claims without structured findings through the
patient-oriented `displayText` helper. This rounds every decimal to one place
and coarsens ISO dates to early/mid/late month. A mocked clinician answer with
`48.234 ms` and `2026-03-01` therefore displayed `48.2 ms` and `early March`.

This predates Claude's latest fix, but remains relevant to the improved Q&A path.
Use clinician-specific display formatting: preserve exact comparison dates and
source-supported numbers/units; put original machine text behind Technical
details. Do not mutate the checked claim or use a blanket rounding regex.
Add a Q&A-specific browser check, not just a clinician-brief card check.

### 2. Medication-only fallback questions lose relevant facts — medium

`aura_agent/templates.py:14` selects findings, check-in summaries/runs, gaps and
context. It never selects ordinary medication-routine facts from `get_decisions`.
A deterministic probe with a delivered medication fact and the question
"Were any medication doses missed?" selected other findings, not that fact.
The approved canned routine query does not have this same selection path.

Include explicitly relevant routine/held-review/optional-channel facts in the
free-question fallback, still describing them as related facts rather than
pretending to answer the investigation. Use token-aware matching; current
substring matching can select unrelated signals (for example "steps" in
"steps taken to review the record"). Test both relevant inclusion and unrelated
exclusion, plus a record with no matching facts.

### 3. Breathing placeholder lifetime is attached to preview, not AI — medium

The graphic is `#recap-placeholder` in `aura_ui/index.html:63`; the WebP is a static
illustration animated by CSS, not a video. `styles.css:268` applies a three-second
pulse/scale cycle. At `agent.js:241`, it appears only when no recap exists.
`agent.js:247` immediately renders the cached/deterministic preview, and the
patient render at line234 hides it unconditionally. The later model POST at
line251 is still pending.

Mocked browser reproduction with the actual UI script/CSS:

- Preview delay300 ms; model delay2000 ms.
- Graphic visible306 ms, not through the model wait.
- CSS cycle3 seconds: the graphic disappears well before a complete cycle.
- Cached refresh keeps it hidden; no new full-screen loading state is expected.
- Reduced-motion setting correctly disables the CSS animation.
- A BLOCKED preview returns before the hide line: the placeholder remains visible
  while the interface says safety takes priority. Initial GET failure also has
  no explicit placeholder cleanup in the catch path (code inspection).

Recommendation: separate the decorative welcome motion from actual loading
status. Keep available summary text visible immediately. Use a gentler roughly
six-second decorative cycle and, if desired, a first-entry2–3-second visual
transition without blocking content/help. A small motif can continue beside the
preview while wording is actually pending, with honest status text.

Always stop loading presentation on blocked/offline/error/stale/role-change
paths. Safety/resources must never wait for animation or a minimum display timer.
Do not force a loading splash on every cached refresh or hide an existing recap
just to show the artwork. These timing choices are UI recommendations, not
clinical parameters or changes already implemented.

### 4. One-minute retry promise is not reliable — low

`SystemSettings.reserve` emits the same `demo_budget` kind for minute and hour
limits. `aura_app/agent.py:195` nevertheless says "Try again in a minute." At
60/hour exhaustion, availability may take much longer and other viewers share
the quota. Use neutral wording or derive a retry-after value from the actual
limiting window. Keep quotas unchanged. Surface the reason accessibly: currently
the disclosure is often only the badge's title tooltip, which is weak on phones.

### 5. Show useful agent steps, not just tool names — optional minor polish

The existing trace already stores tools, selected windows and verifier counts.
A concise human-readable line beneath Q&A can show those facts. For example:
"Read sleep and activity → compared the selected periods → checked the claims."
Use exact trace windows and actual outcomes/counts; never expose hidden
chain-of-thought or label a fallback as a completed investigation. This improves
the demo's agentic story without introducing agent autonomy.

## Verification

- Full existing Python suite: **295 PASS / 348.788 seconds**.
- Existing hosted synthetic browser suites: agent5 + cards4 = **9 checkpoints PASS**.
- Mocked UI probe: preview/animation lifetime, cached-refresh behavior, reduced
  motion, clinician number/date formatting and blocked-placeholder behavior
  reproduced; zero page errors in the final probe.
- Selector probe: delivered medication fact available but not selected.
- No new live Q&A reliability claim. Historical19/20 headline numbers do not
  measure this path or current v11.

Commands:

```sh
.venv/bin/python -m unittest discover -s tests -q
NODE_PATH=/home/makodev58/rendertest/node_modules \
LD_LIBRARY_PATH=/home/makodev58/rendertest/libs/usr/lib/x86_64-linux-gnu \
.venv/bin/python tests/browser/run.py --hosted --port 8026 \
  --artifacts /tmp/aura-claude-review-browser --suite agent.cjs cards.cjs
```

Temporary diagnostic script: `/tmp/aura-review-animation.cjs` (not a committed
test or production code). Initial probe fixture lacked the required guard
fingerprint and timed out; corrected fixture completed. Browser launch needed
host permission. Neither diagnostic issue is counted as an application failure.

## Verdict

Accept the direction and clinician-report separation for the synthetic demo.
Recommend the narrow follow-ups above before declaring Q&A presentation polished.
No engine redesign, quota increase or new feature milestone is warranted.
