# AURA — implementation and trust boundaries

M7 synthetic engineering prototype. Diagram reflects the code, not clinical validation.

```mermaid
flowchart TD
  UI[Patient web UI: presentation only] --> API[FastAPI / application services]
  API --> DB[(Repository protocols / development SQLite)]
  API --> GATE[Safety gate: resolved inputs or fail closed]
  GATE --> SAFETY[aura_safety: authoritative deterministic policy]
  API --> LONG[aura_longitudinal: anchor + rolling + context]
  SAFETY --> INTENT[Committed communication intent: safety precedence]
  LONG --> INTENT
  INTENT --> WORD[aura_communication: bounded phrasing contract]
  WORD --> OPTIONAL[Optional model adapter: no state ownership]
  OPTIONAL --> VALID[Deterministic validation / fixed fallback]
  WORD --> VALID
  VALID --> UI
  SAFETY --> PIN[Separate pinned resources / built-in fallback]
  PIN --> UI
  INTENT --> DB
  VALID --> DB
  API --> AUDIT[Linked application / safety / wording audit]
  AUDIT --> DB
  subgraph Evaluation_only
    PLAN[Simulation Data Agent: offline planner or optional JSON gateway]
    PLAN --> SPEC[Validated structured synthetic specification]
    SPEC --> GEN[Seeded numeric generator]
    GEN --> FILTER[Observable-event allowlist]
    GEN --> TRUTH[Hidden labels / expected outcomes: evaluation only]
    FILTER --> DRIVER[Development fixture driver]
  end
  DRIVER --> API
```

Safety-relevant input reaches the safety boundary before longitudinal/conversational
processing. Unknown assessment fails closed; no model decides policy. Public hosted
demo accepts only named fixtures, rejects other input before persistence, disables
models, disallows patient/anchor creation, and gives each browser a separate synthetic
workspace. No authenticated care or real-data intake is provided.

Only observable values, structured patient reports, explicit context links, and
resolved fixture proposals cross the evaluation boundary. The production modules do
not import `aura_simulation`; scenario labels and latent truth cannot affect decisions.
DEMO2 mutates hidden fields and checks identical observable frames and committed
states/actions. DEMO16 checks the import boundary.

The application adapter forwards production-assessed newly meaningful signal evidence
to the **existing** held-record reopening API. No domain threshold or rule is copied.
Anchors require explicit commands. Snapshot selection is a temporary UI preview, not
approval or transmission. Fixture resources are unverified and contain no invented
crisis contacts. Live generation requires future consent/content governance.
