# Architecture slide images

Healthcare Challenge Statement 2, Scenario 1: Mental Health Maintenance for
Working Adults on Antidepressants.

**Current (2026-10-14, implementation audit at `90e31ea`): slides 11–13 are native PowerPoint diagrams**
built by [`../deck/native_diagrams.py`](../deck/native_diagrams.py): editable boxes and
connector arrows glued to the boxes' connection points, so moving a box in PowerPoint
keeps its arrows attached. The PNGs here are ReportLab drawings of those same native
shapes, with embedded Nunito, used by the HTML slides and future video rebuilds.
The earlier versions were LibreOffice renders. This export was visually inspected
and text bounds checked; PowerPoint/LibreOffice rendering is not newly verified.
The audit clarifies provider configuration, the 90-second loop budget/30-second
provider timeout, normal synthetic ingestion, fixed medication content and
resources that are rendered without a model. Patient-input assessment may use one.

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
  call may use the same model/provider. A failed draft uses related recorded facts
  when available; blocked/stale requests suppress ordinary content. The elapsed
  budget is checked between calls, not a strict 90-second HTTP-response guarantee.
- **Safety:** evidence proposals enter deterministic policy. The application
  follows its result before ordinary communication. T4, degraded and offline
  fail-closed prohibit generated wording; resource rendering uses no model and
  has a built-in fallback. Initial detection and the communication response can
  involve model latency, so the drawing makes no blanket zero-wait guarantee.

Future institutional hosting is labelled in the overview footer, without a
component or arrow implying an implemented deployment. No production authentication,
automatic sharing, clinical outcomes, real wearable connector or care-action tool
is depicted. Safety resource content still requires review.

Re-export all three current diagrams from their shared native source using a
tooling environment with python-pptx, reportlab, fonttools, brotli and pymupdf:

```sh
python docs/presentation/deck/reconcile_architecture.py
```

No application dependency changes. This updates the existing deck's native slides
11–13, diagram/slide PNGs and `assets/aura-health-architecture-reviewed.pdf` together.
Historical SVG/export scripts remain for provenance, not current diagram rebuilds.
See [`../../submission/ARCHITECTURE_REVIEW.md`](../../submission/ARCHITECTURE_REVIEW.md).
User approval and final release checks remain pending; video frames need a separate rebuild.
