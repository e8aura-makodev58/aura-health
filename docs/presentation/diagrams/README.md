# Architecture slide images

Healthcare Challenge Statement 2, Scenario 1: Mental Health Maintenance for
Working Adults on Antidepressants. Created 2026-10-13 by Codex for submission
work-plan task #8 / X1. Ready for deck-author review; not a PPTX upload by itself.

| Diagram | Editable source | Slide image | PNG bytes |
|---|---|---|---:|
| System overview and trust boundaries | [system-overview.svg](system-overview.svg) | [system-overview.png](system-overview.png) | 290724 |
| Aura-Agent investigation loop | [agent-investigation.svg](agent-investigation.svg) | [agent-investigation.png](agent-investigation.png) | 235065 |
| Safety precedence and pinned resources | [safety-precedence.svg](safety-precedence.svg) | [safety-precedence.png](safety-precedence.png) | 210503 |

Every image is **1920 × 1080, exact 16:9**. Use the PNG at full slide width or the
SVG for scalable text and shapes. The background and palette follow `aura_ui/styles.css`.
Original vector shapes and typography were drawn from the repository architecture;
no external artwork or generative-image provenance is claimed. No scripts, remote
fonts, external images or embedded application screenshots are in these SVGs.

Source: [ARCHITECTURE_DOCUMENT.md](../../submission/ARCHITECTURE_DOCUMENT.md),
inspected implementation `3d95a66`; current Codex branch `f5f06d1` has the same
domain/agent behavior. The current configured model was independently checked as
DeepSeek / deepseek-flash on 2026-10-13. Do not relabel that as Tencent hosting.

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

The deck author should insert these into `docs/submission/assets/aura-health-deck.pptx`
and inspect the exported slides. User approval and final release checks remain pending.
