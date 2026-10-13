# Submission asset register

Status date 2026-10-13. No assets are marked READY without inspection and approval.
Owners below are proposed responsibilities, not evidence that work was completed.

| Deliverable | Location | State | Next action / owner |
|---|---|---|---|
| Form text | `FORM_CONTENT.md` | DRAFT | User approves; reviewer checks claims/versions |
| Form constraints | `REQUIREMENTS.md` | CAPTURED | Verify against live form before uploading |
| Cover image | `assets/aura-cover.png` | AWAITING_USER | User generates with Miora; reference screenshots in `docs/presentation/screenshots/v2/`; review at thumbnail size |
| Demo video | Actual URL in `manifest.json` | MISSING | User/presenter records 7-minute script; confirm signed-out access |
| Development history bundle | `assets/development-history.pdf` | MISSING | User supplies genuine logs plus≥3 screenshots; agent sanitizes/packs only with authority |
| Architecture PPTX | `assets/aura-health-deck.pptx` | REVIEW_PENDING | Claude export exists:18 slides/2,757,539 bytes; re-render companion overview and inspect/approve |
| Architecture slide diagrams | `../presentation/diagrams/` | REVIEW_PENDING | Codex: three editable SVGs +1920×1080 PNGs,2026-10-13; see diagram README; Claude inserts into deck and reviews |
| Live demo URL | `manifest.json` | PARTIALLY_CHECKED | Health/status and fresh signed-out browser session/Q&A checked2026-10-13; final A–F walkthrough pending |
| GitHub URL | `manifest.json` | ACCESS_BLOCKED | Anonymous URL returned HTTP404 on2026-10-13; user/reviewer to arrange judge access or correct link |
| Optional social post | Actual URL in `manifest.json` | NOT_STARTED | User decides platform/publication; all 4 hashtags |
| Release/approval | `manifest.json` | PENDING | Final tested commit plus user approval; no final tag created |

For each final upload record creator/tool, creation date, file name, bytes,
implementation commit shown, reviewer and approval date here. For artwork include
provenance/licensing; for screenshots record actual development-session provenance.
Do not insert invented evidence details merely to fill the table.

PPTX exists; cover/history uploads and final video URL remain missing. Eight user-
supplied genuine CodeBuddy/Miora screenshots are in `screenshots/`; they do not
alone satisfy the combined chat/history upload. Silent walkthrough exists outside
Git; voice-over, publication and final access review remain human-owned.

Codex diagrams: original vector drawings based on implemented architecture,
created2026-10-13; code snapshot `f5f06d1` (architecture source inspected at
`3d95a66`). SVGs4956/4560/6403 bytes and PNGs235065/210503/290724 bytes for
agent/safety/overview respectively. Exact16:9 dimensions verified, labels fitted
and rendered images inspected. No external artwork; user/deck review pending.

Overview updated against integrated companion `f37af0c` in Codex candidate68372f3:
297,460 PNG bytes,1920×1080. Source/renderer in the diagram folder. Medication info,
read-only `/companion` and safety-first `/medication/ask` now shown. **Claude must
re-render the deck**; existing deck artifact is not updated by changing the PNG.
Other two diagrams unchanged. Current X5 outcomes/blockers are in the ledger;
do not promote candidate checks to final release approval.

Preliminary release verification:303 Python tests and7 assertions in two local
browser suites passed on `f5f06d1`. Live rehearsal1 partial generated /2 fallbacks;
see `EVIDENCE_LEDGER.md`. These do not approve a final merged release.

Consolidated candidate `495087d`,2026-10-13: independent18 browser checks PASS
(companion/Q&A-display/hosted-M7) on8036; actual merged count-contract smoke PASS;
live signed-out normal/safety companion reads PASS without requested generation.
GitHub anonymous access remains404. Screenshot evidence receipt at
`docs/submission/screenshots/` is user-reported; bundling/provenance review belongs
to its assigned owner. No narration, screenshots or runtime files changed here.
Full candidate suite327 PASS/469.072s; a changed-question/reused-run-ID safety-
assessment gap was separately reproduced and remains open. Readiness blockers
and newer-main version limits are in `EVIDENCE_LEDGER.md`.
