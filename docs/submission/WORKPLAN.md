# Submission work plan — 13 to 15 October 2026

Owner of this plan: Claude (coordination). User approves scope, merges, deploys and submits.
Target: everything READY on **15 Oct**; deadline **16 Oct** (buffer day).

Source of the findings: Claude's review of this folder on 13 Oct (see root `HANDOVER.md`).
Every agent: pull first, edit only the files assigned to you, commit with explicit paths,
add a Log entry to `HANDOVER.md`. Do not edit another agent's files; ask in `HANDOVER.md`.

## Decisions taken (user, 13 Oct: "fix all of those findings")

1. **Challenge:** Healthcare track (NTU LKC Medicine), **Challenge Statement 2 "AI Healthier
   Every Day", Scenario 1 "Mental Health Maintenance for Working Adults on Antidepressants"**.
   Every artifact opens with this. Mapping lives in `CHALLENGE_MAPPING.md`.
2. **Title:** `AURA Health` everywhere (repo name stays `aura-health`).
3. **One deck** serves as the presentation and the required "Architecture Diagram PPT":
   `assets/aura-health-deck.pptx` (≤10 MB) contains product, architecture and trust-boundary
   slides. `ARCHITECTURE_DECK.md` content becomes those slides.
4. **No relapse prediction or advice** is a deliberate safety choice, presented as such.
5. **Business value** adds clearly labelled *pilot metrics we would measure* (targets, not results).
6. **Demo Q&A question:** "When did sleep timing change, and was anything reported around then?"
7. Personal account email is removed from public files.

## Assignments

| # | Finding / task | Owner | Files | Due |
|---|---|---|---|---|
| 1 | Name Challenge 2 Scenario 1 at the start of every artifact | Claude | `FORM_CONTENT.md`, `VIDEO_SCRIPT.md`, deck | 13 Oct |
| 2 | Map sponsor's features/qualities: covered vs roadmap | Claude | `CHALLENGE_MAPPING.md` (new) | 13 Oct |
| 3 | Frame no-relapse-prediction as safety design | Claude | `FORM_CONTENT.md`, `CHALLENGE_MAPPING.md` | 13 Oct |
| 4 | Title → AURA Health | Claude | `FORM_CONTENT.md`, `manifest.json` | 13 Oct |
| 5 | Pilot metrics (labelled targets) | Claude | `FORM_CONTENT.md` | 13 Oct |
| 6 | Rewrite video script for the new flow | Claude | `VIDEO_SCRIPT.md` → points to `../presentation/SCRIPT.md` | 13 Oct |
| 7 | Rehearsal check of the demo question (≤5 live runs, report honestly) | Codex | `EVIDENCE_LEDGER.md` | 14 Oct |
| 8 | Architecture diagrams as slide images (overview + agent loop + trust boundaries) | Codex | `docs/presentation/diagrams/*.svg` and `.png` | 14 Oct |
| 9 | Remove personal email from public files | Claude | `README.md`, `REQUIREMENTS.md` | 13 Oct |
| 10 | Artwork provenance + development-history bundle | User (genuine screenshots) → CodeBuddy (assemble PDF) | `assets/development-history.pdf` | 14 Oct |
| 11 | Cover image 16:9 (≤1 MB; 1920×1080 master, 384×216 export) | CodeBuddy with Miora | `assets/aura-cover.png` | 14 Oct |
| 12 | Q&A suggestion-chip styling | Claude | `aura_ui/styles.css` | 13 Oct |
| 13 | "When things changed" strip: oversized labels | CodeBuddy | `aura_ui/` (branch `improve/UI_UX`) | 14 Oct |
| 14 | Presentation script (5–8 min) | Claude drafts → user approves | `../presentation/SCRIPT.md` | 13 Oct |
| 15 | Deck built from approved script + screenshots + Codex diagrams | Claude | `assets/aura-health-deck.pptx` | 14 Oct |
| 16 | Video: screen-recorded walkthrough following the script | Claude records screens; **user narrates** (no voice tools here) | `../presentation/video/` (not in Git if large) | 15 Oct |
| 17 | Release checks: full tests, signed-out link checks, ledger/register/manifest, preflight | Codex | `EVIDENCE_LEDGER.md`, `ASSET_REGISTER.md`, `manifest.json` | 15 Oct |
| 18 | Final submission | User | form | 15–16 Oct |

## Kickoff prompts

**Codex:**
> Read `docs/submission/WORKPLAN.md`. Your tasks are #7, #8 and #17. For #8, draw from
> `docs/submission/ARCHITECTURE_DOCUMENT.md`: three 16:9 diagrams (system overview with trust
> boundaries, the Aura-Agent investigation loop, safety precedence/pinned resources), warm
> off-white background, AURA palette, large readable labels, SVG plus 1920×1080 PNG in
> `docs/presentation/diagrams/`. No runtime changes, no deploys, no quota changes. For #7 use at
> most 5 live runs of the demo question and record every outcome, including fallbacks. Edit only
> your assigned files; log in `HANDOVER.md`.

**CodeBuddy (branch `improve/UI_UX`):**
> Read `docs/submission/WORKPLAN.md` and `docs/submission/COVER_BRIEF.md`. Your tasks are #11
> (cover image, with Miora: title "AURA Health", subtitle "Context between appointments", use the
> real screenshots in `docs/presentation/screenshots/` as reference, export 1920×1080 and 384×216
> PNG under 1 MB to `docs/submission/assets/`) and #13 (the "When things changed" strip in the
> clinician view has oversized "1", "2" and date labels; make them match the card text size). Keep
> genuine screenshots of your CodeBuddy and Miora sessions for #10. Do not merge or deploy.
