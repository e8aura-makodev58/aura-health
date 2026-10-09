# AURA — implementation and trust boundaries

M7 synthetic engineering prototype. Diagram reflects the code, not clinical validation.

```mermaid
flowchart TD
  UI[Patient / clinician demo UI: presentation only] --> API[FastAPI / application services]
  API --> DB[(Repository protocols / development SQLite)]
  API --> GATE[Safety gate: resolved inputs or fail closed]
  RULES[Demo curated D2 rules: raise-only proposals] --> GATE
  SEMANTIC[Demo semantic D4 model: raise-only proposals] --> GATE
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
  API --> AGUARD[Agent guard: valid NORMAL, assessed input, online]
  AGUARD --> AGENT[aura_agent: bounded read-only model/tool loop]
  AGENT --> READ[Immutable patient-scoped committed facts]
  DB --> READ
  READ --> AGENT
  AGENT --> GROUNDED[Citation / numeric / structured finding validation]
  GROUNDED --> VERIFIER[Separate model claim verifier: no policy ownership]
  VERIFIER --> CHECKED[Supported claims only / labelled extraction]
  CHECKED --> RACE[State and provider revision recheck]
  RACE --> UI
  RACE --> TRACE[Append-only agent_runs + application audit]
  TRACE --> DB
  API --> WORKFLOW[Confirmed synthetic intake and workflow service]
  WORKFLOW --> DB
  API --> AUDIT[Linked application / safety / wording audit]
  AUDIT --> DB
  subgraph Evaluation_only
    PLAN[Simulation Data Agent: offline planner or optional JSON gateway]
    LIFE[Demo life director: model plan / offline keyword fallback] --> LIFESPEC[Strict life plan: no numeric telemetry]
    LIFESPEC --> GEN
    PLAN --> SPEC[Validated structured synthetic specification]
    SPEC --> GEN[Seeded numeric generator]
    GEN --> FILTER[Observable-event allowlist]
    GEN --> TRUTH[Hidden labels / expected outcomes: evaluation only]
    FILTER --> DRIVER[Development fixture driver]
  end
  DRIVER --> API
  WORKFLOW --> LIFE
```

Safety-relevant input reaches the safety boundary before longitudinal/conversational
processing. Unknown assessment fails closed; no model decides policy. Public hosted
demo accepts bounded synthetic manual/import/context and safety-gated text alongside
named fixtures. It allows operator-configured synthetic-only models, disallows
public patient/anchor creation, and gives each browser a separate synthetic
workspace. No authenticated care or real-data intake is provided.

Only observable values, structured patient reports, explicit context links, and
resolved fixture proposals cross the evaluation boundary. Production event/safety/
longitudinal modules do not import `aura_simulation`; scenario labels and latent
truth cannot affect decisions. The explicit synthetic-only workflow adapter
invokes the generator and submits observable events through the same application
service; plans/truth remain in workflow traces.
DEMO2 mutates hidden fields and checks identical observable frames and committed
states/actions. DEMO16 checks the import boundary.

The application adapter forwards production-assessed newly meaningful signal evidence
to the **existing** held-record reopening API. No domain threshold or rule is copied.
Anchors require explicit commands. Snapshot selection is a temporary UI preview, not
approval or transmission. Fixture resources are unverified and contain no invented
crisis contacts. Real-patient live generation requires future consent/content governance.

The read-only product agent is separate from the Simulation Data Agent. It may
investigate and draft, never decide safety/drift, move anchors, establish context
credibility, authorize interruption or share records. No write tools exist.
Tools exclude latent truth and use opaque model-facing source aliases; displayed
citations still identify real committed records. Offline extraction is not AI.
See [current agent/intake/simulator implementation and limits](APPROVED_AGENT_AND_SIMULATOR_IMPLEMENTATION.md).
