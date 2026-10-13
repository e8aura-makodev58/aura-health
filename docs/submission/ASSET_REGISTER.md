# Submission asset register

Status date 2026-10-13. No assets are marked READY without inspection and approval.
Owners below are proposed responsibilities, not evidence that work was completed.

| Deliverable | Location | State | Next action / owner |
|---|---|---|---|
| Form text | `FORM_CONTENT.md` | DRAFT | User approves; reviewer checks claims/versions |
| Form constraints | `REQUIREMENTS.md` | CAPTURED | Verify against live form before uploading |
| Cover image | `assets/aura-cover.png` | MISSING | User/Miora designer generates; review at thumbnail size |
| Demo video | Actual URL in `manifest.json` | MISSING | User/presenter records 7-minute script; confirm signed-out access |
| Development history bundle | `assets/development-history.pdf` | MISSING | User supplies genuine logs plus≥3 screenshots; agent sanitizes/packs only with authority |
| Architecture PPTX | `assets/aura-architecture.pptx` | MISSING | Deck author uses outline/diagram; exports actual PPTX; inspect all slides |
| Live demo URL | `manifest.json` | HEALTH_CHECKED | `/health` returned ok / synthetic_only=true on 2026-10-13; full signed-out walkthrough still needed at release |
| GitHub URL | `manifest.json` | CONFIGURED | Origin matches repository; verify anonymous judge access at release |
| Optional social post | Actual URL in `manifest.json` | NOT_STARTED | User decides platform/publication; all 4 hashtags |
| Release/approval | `manifest.json` | PENDING | Final tested commit plus user approval; no final tag created |

For each final upload record creator/tool, creation date, file name, bytes,
implementation commit shown, reviewer and approval date here. For artwork include
provenance/licensing; for screenshots record actual development-session provenance.
Do not insert invented evidence details merely to fill the table.

Required upload files are not yet produced. Markdown outlines and marketing
clips do not satisfy the PPT/video/history upload requirements.
