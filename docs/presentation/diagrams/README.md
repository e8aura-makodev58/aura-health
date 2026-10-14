# Architecture slide images

Healthcare Challenge Statement 2, Scenario 1: Mental Health Maintenance for
Working Adults on Antidepressants.

**Current (2026-10-14, Claude): the deck's slides 11–13 are native PowerPoint diagrams**
built by [`../deck/native_diagrams.py`](../deck/native_diagrams.py): editable boxes and
connector arrows glued to the boxes' connection points, so moving a box in PowerPoint
keeps its arrows attached. The PNGs here are LibreOffice renders of those slides (used by
the video and the HTML slides). Content updated to the current build: provider-configurable
model gateway with an operator-chosen model and reasoning level, 90-second agent run
budget, curated medication content, and "no alerts are sent" on the safety slide.

The original SVGs (Codex, 2026-10-13) are kept as history; their wording is older
(for example "DeepSeek active", 50-second budget) and they no longer match the PNGs.

## How to explain the diagrams

- **Overview:** dashed containers mark computational/trust boundaries, not
  separately deployed microservices. Solid arrows summarize implemented calls and
  data flow; detailed event routes remain in the architecture document. Only
  observable synthetic events enter the application from the evaluation plane.
  Hidden labels never feed decisions. The browser does not calculate policy.
- **Agent loop:** this is the question-directed record Q&A path. The model can
  choose tools and windows and repeat within limits. Automatic recaps have more
  constrained selection/wording. Tools read records or compute descriptive
  comparisons; only the application persists the run and audit. A separate verifier
  call may use the same model/provider. A failed draft uses recorded facts.
- **Safety:** evidence proposals enter deterministic policy. The application
  follows its result before ordinary communication. T4, degraded and offline
  fail-closed prohibit generation; pinned resources do not wait for generated text
  or depend exclusively on live registry availability.

Future institutional hosting is labelled in the overview footer, without a
component or arrow implying an implemented deployment. No production authentication,
automatic sharing, clinical outcomes, real wearable connector or care-action tool
is depicted. Safety resource content still requires review.

Rendered with installed Chromium through Playwright (no repository dependency
changes). Inspected at slide size; text fitted within cards and canvas; PNG dimensions
verified with `file`. SVGs are the durable sources for subsequent exports.

Re-export the overview from its durable SVG with the existing Playwright environment:

```sh
NODE_PATH=/home/makodev58/rendertest/node_modules \
LD_LIBRARY_PATH=/home/makodev58/rendertest/libs/usr/lib/x86_64-linux-gnu \
node docs/presentation/diagrams/export_overview.cjs
```

Paths above describe the development machine, not a new repository dependency.

The deck author should insert these into `docs/submission/assets/aura-health-deck.pptx`
and inspect the exported slides. User approval and final release checks remain pending.
