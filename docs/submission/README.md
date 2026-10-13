# AURA Health — Tencent Cloud Hackathon Singapore 2026 submission

Canonical preparation folder for the **Healthcare Track**. Created 2026-10-13
from the submission form supplied by the user. Status: **DRAFT — not submitted**.
Target readiness 2026-10-15; recorded project deadline 2026-10-16. Confirm the
organizer's exact closing time/timezone before relying on a last-day upload.

## Start here

| File | Purpose |
|---|---|
| [REQUIREMENTS.md](REQUIREMENTS.md) | Current form requirements, sizes and account instructions |
| [WORKPLAN.md](WORKPLAN.md) | Who does what by when (13–15 Oct) |
| [CHALLENGE_MAPPING.md](CHALLENGE_MAPPING.md) | Chosen challenge and feature-by-feature fit |
| [FORM_CONTENT.md](FORM_CONTENT.md) | Copy-ready title, blurb, four-part description and URLs |
| [manifest.json](manifest.json) | Machine-readable status, links, expected upload paths and approval |
| [ASSET_REGISTER.md](ASSET_REGISTER.md) | Ownership/status of required deliverables |
| [VIDEO_SCRIPT.md](VIDEO_SCRIPT.md) | Seven-minute recording plan, including substantive agent use |
| [ARCHITECTURE_DECK.md](ARCHITECTURE_DECK.md) | Content/notes for a single architecture PPTX |
| [architecture.mmd](architecture.mmd) | Editable trust-boundary diagram source |
| [COVER_BRIEF.md](COVER_BRIEF.md) | Miora design brief and image export requirements |
| [EVIDENCE_GUIDE.md](EVIDENCE_GUIDE.md) | Genuine conversation history plus at least 3 screenshots in one file |
| [EVIDENCE_LEDGER.md](EVIDENCE_LEDGER.md) | What numerical claims are supported, and their limits |
| [assets/README.md](assets/README.md) | Where approved upload files belong |

The previous `docs/SUBMISSION_DRAFT.md` is background, not the final form copy.
The older demo script/brief cannot downgrade required fields in the current form.

## Instructions for every agent

1. Read root `HANDOVER.md`, this file and `REQUIREMENTS.md` before submission work.
2. Preserve the bugs/minor-updates freeze. Submission preparation is now explicitly
   authorized; it does not retrospectively accept M7 or authorize new product features.
3. Use this folder, not competing submission drafts. Edit only assigned files;
   pull/re-read before edits and record changes in the root handover.
4. Distinguish **implemented now**, **synthetic engineering evidence**, **intended
   final-product work**, and **standing exclusions**. Never turn future capability
   into a shipped claim or a clinical benefit into a measured outcome.
5. Show the real agent: question-directed tool selection, chosen windows,
   returned analysis, citations and independent verification. A recap alone is
   not the whole agentic story. Models do not own longitudinal/safety state.
6. Preserve errors/fallbacks in evidence. Never manufacture chat screenshots,
   successful answers, patient endorsements, timing results or clinical validation.
7. Keep raw chat exports, tokens/keys, cookies, account details, provider errors
   and the Tencent-internal supplied PDF out of public assets and Git. Use ignored
   `private/` for working originals; commit only sanitized approved artifacts.
8. Capture CodeBuddy/WorkBuddy/Miora evidence from genuine development sessions.
   The user controls those tools; do not launch them automatically.
9. Track each artifact in `ASSET_REGISTER.md` and `manifest.json`: path, creator,
   date, implementation commit, size and review state. No placeholder is READY.
10. Do not upload the form, publish a video/social post, change account settings,
    widen quotas or redeploy without the user's separate instruction.

## Completion order

- Review form text and numerical claims.
- Produce the cover PNG, architecture PPTX and one history/screenshots bundle.
- Record/upload the 5–8-minute walkthrough using the approved current build;
  add its viewer-accessible link. Marketing clips may be inserts, not substitutes.
- Check demo and GitHub links as a signed-out viewer. Confirm source repository
  access, cookies/session reset and absence of operator-key requirements.
- Run the full suite and essential demo/fallback checks on the release commit;
  record versions/results, inspect uploaded artifacts, then run:

```sh
.venv/bin/python docs/submission/preflight.py
# Once all deliverables are supplied and approved:
.venv/bin/python docs/submission/preflight.py --require-ready
```

Set manifest `status` to `READY` only after all files/links/release checks and
the user's approval; keep it `DRAFT` while anything remains unresolved.
The script makes **no network calls or writes**. Passing metadata checks is not
human claims/design review, proof of link permissions or final acceptance.
At present it should report missing uploads/video/approval, not claim readiness.

## Final operator steps

Use the team's submitting Google account, selected by the human operator.
The form records the Google account's name/email/photo with uploads/submission.
Confirm account and file permissions before submitting. Paste only the copy blocks
from `FORM_CONTENT.md`; remove all drafting notes and unresolved placeholders.
The user performs the final submission and saves its confirmation. Record actual
submission time, release commit and confirmation location only after submission.

The optional social post must use all four hashtags in `REQUIREMENTS.md` and
include a genuine published link. Leave it blank if no post is authorized.
