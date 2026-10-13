# Voice-over sheet — `aura-health-walkthrough-novoice.mp4` (5:59)

Read the narration from [`../SCRIPT.md`](../SCRIPT.md) against these timestamps. The video has a
silent audio track; record your voice separately and lay it over (any editor, e.g. CapCut), or
record while the video plays. Pace: calm, about 150 words a minute.

| Video time | On screen | Say (script scene) |
|---|---|---|
| 0:00–0:25 | Cover, then the chosen challenge | Scene 1 · The challenge |
| 0:25–0:53 | The problem | Scene 2 · The problem |
| 0:53–1:22 | Landing, "Take a breath", the summary (phone) | Scene 3 · A calm start |
| 1:22–2:06 | Today's dose → Skipped → Side effects; My medication → missed dose; "Can I take ibuprofen with it?" → abstention | Scene 4 · My medication, my day |
| 2:06–2:38 | Demo guide → flu → new summary → a small idea for today | Scene 5 · Something changes |
| 2:38–2:55 | Prepare for my appointment → missed dose with its reason | Scene 6 · Ready for the appointment |
| 2:55–3:34 | Clinician view → AI headline → typed question → *How AURA looked* → cited answer | Scene 7 · The agent at work |
| 3:34–3:56 | I want to mention something → safety example → safety panel | Scene 8 · Safety first |
| 3:56–4:50 | Architecture, agent loop, safety precedence, trade-offs | Scene 9 · How it's built |
| 4:50–5:15 | Six features: built / in the demo / partial | Scene 10 · Fit with the challenge |
| 5:15–5:35 | How we built it (add your CodeBuddy/Miora screenshots to slide 16 first) | Scene 11 · How we built it |
| 5:35–5:59 | Impact (targets), roadmap, close | Scene 12 · Impact and close |

Honesty notes for the narration:
- Everything on screen is synthetic demo data and a real live run; AI text was not edited.
- In scene 7 the first question attempt fell back (shown in the trail as a stop); the video uses
  the second attempt, which completed. Do not describe this as a success rate.
- Slide 16 still has the placeholder for genuine CodeBuddy/Miora session screenshots; re-render
  the deck and re-assemble after adding them (`tools/assemble.py`).

Rebuild: `tools/record.cjs` (live scenes 3–8), `tools/record_desk.cjs` (scene 7 only),
`tools/bg.cjs` (scene backgrounds), `tools/assemble.py` (cuts and joins; needs ffmpeg).
