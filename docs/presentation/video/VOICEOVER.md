# Voice-over sheet — `aura-health-walkthrough-novoice.mp4` (5:58)

> **Alternative (user choice, 2026-10-14):** song for the opening and close, voice-over only for the middle — see [`SONG_CUT_PLAN.md`](SONG_CUT_PLAN.md).

The app scenes are a real recording of the live **in-app guided story** ("Play the 3-minute story"),
so the video shows exactly what judges can click. Read the narration from
[`../SCRIPT.md`](../SCRIPT.md) (v4) against these timestamps. The video has a silent audio track;
record your voice and lay it over, then add your Miora intro/outro clips. Pace: calm, ~150 words/min.

| Video time | On screen | Say (script scene) |
|---|---|---|
| 0:00–0:25 | Cover, then the chosen challenge | 1 · The challenge |
| 0:25–0:53 | The problem | 2 · The problem |
| 0:53–1:29 | Landing → Play the 3-minute story → Start → "Take a breath" → the summary | 3 · A calm start |
| 1:29–2:07 | Today's dose (Skipped → side effects), the leaflet answer, "Can I take ibuprofen with it?" → honest reply | 4 · My medication, my day |
| 2:07–2:25 | Visit note with the missed dose and its reason, Not sent | 5 · Ready for the appointment |
| 2:25–3:05 | Clinician view → the agent's question → first draft didn't pass the checks → *Ask again* → checked answer with *How AURA looked* | 6 · The agent at work (include the fallback line) |
| 3:05–3:28 | Simulated flu → new summary → a small idea for today | 7 · Something changes |
| 3:28–3:55 | Finish card → Show the safety example → note box with the masked example → Send → safety panel → the card explains (no alerts; Reset the demo) | 8 · Safety first |
| 3:55–4:49 | Architecture, agent loop, safety precedence, trade-offs | 9 · How it's built |
| 4:49–5:14 | Six features: built / in the demo / partial | 10 · Fit with the challenge |
| 5:14–5:34 | How we built it | 11 · How we built it |
| 5:34–5:58 | Impact (targets), roadmap, close | 12 · Impact and close |

Honesty notes:
- Synthetic demo data and a real live run; AI text was not edited.
- Re-recorded 2026-10-13 (gpt-6-luna, reasoning medium). Scene 6 shows the first agent draft failing a fact check and a visible *Ask again* that then completed with a checked answer;
  say so (the script's fallback line fits). Don't describe it as a success rate.
- Wait times for AI and the simulation were trimmed; a few seconds of still frame were added
  where the narration needs more time (scenes 5, 6, 7).

Rebuild: `tools/record_tour.cjs <url> <dir> phone|desk`, `tools/bg.cjs`, `tools/assemble_tour.py <outdir>`
(ffmpeg needed). The earlier v2 tools (`record.cjs`, `assemble.py`) are kept for reference.
