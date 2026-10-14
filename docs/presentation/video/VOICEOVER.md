# Voice-over sheet — combined video (draft 6:07; about 6:23 with intro and outro)

**Current plan (2026-10-14):** first half `aura-health-part1-voiceover-novoice.mp4` (3:26) with your
voice-over; second half `aura-health-landscape-demo-novoice.mp4` (2:40), a continuous live take in
PC landscape, under the song. Joined draft: `aura-health-combined-draft-novoice.mp4`. The voice-over
text, timed to the second, is in [`SONG_CUT_PLAN.md`](SONG_CUT_PLAN.md) (sections 1–10).

Each table gives the time inside the file and the time in the finished video (after the 8-s Miora intro). Section starts were checked against frames of the actual files.

### First half · your voice (record against `aura-health-part1-voiceover-novoice.mp4`)

| Part-1 file | Final video | On screen | Say (section) |
|---|---|---|---|
| — | 0:00–0:08 | Miora intro | — |
| 0:00–0:27 | 0:08–0:35 | Cover, the problem, what AURA does | 1 |
| 0:27–0:54 | 0:35–1:02 | Guided story starts: breath, short summary | 2 |
| 0:54–1:16 | 1:02–1:24 | Skipped dose + reason; leaflet answer; "Can I take ibuprofen?" → honest reply | 3 |
| 1:16–1:29 | 1:24–1:37 | Appointment note, Not sent | 4 |
| 1:29–1:58 | 1:37–2:06 | Clinician view → agent: first draft rejected → checked answer | 5 |
| 1:58–2:12 | 2:06–2:20 | Simulated flu, small idea for today | 6 |
| 2:12–2:31 | 2:20–2:39 | Safety example (masked) → safety panel → explanation card | 7 |
| 2:31–2:55 | 2:39–3:03 | Architecture, agent loop | 8 |
| 2:55–3:11 | 3:03–3:19 | Fit with the challenge | 9 |
| 3:11–3:26 | 3:19–3:34 | How we built it | 10 |

### Second half · the song (no voice; `aura-health-landscape-demo-novoice.mp4`)

| Landscape file | Final video | On screen (landscape live take) |
|---|---|---|
| 0:00 | 3:35 | Landing → Play the 3-minute story → intro card |
| 0:13 | 3:48 | Breath, then the short summary |
| 0:28 | 4:03 | Today's dose: Skipped → side effects |
| 0:37 | 4:11 | Medication: leaflet answer |
| 0:51 | 4:25 | "Can I take ibuprofen with it?" → honest reply |
| 1:00 | 4:34 | Appointment note, Not sent |
| 1:08 | 4:43 | Clinician view |
| 1:18 | 4:52 | Agent asked; answer with sources and How AURA looked |
| 1:51 | 5:25 | Simulated flu → new summary, small idea |
| 2:13 | 5:47 | Finish card → Show the safety example (masked) |
| 2:27 | 6:01 | Safety panel + explanation card |
| 2:37–2:40 | 6:12–6:15 | Last frame held |
| — | 6:15–6:23 | Miora outro (song outro "…room for your day") |

Honesty notes: synthetic data; real live runs; AI text not edited. The first half's agent scene shows
the first draft rejected and a visible *Ask again* that then passed (say so, section 5). In the
landscape take the agent passed first time. Waits are trimmed in the first half only; the landscape
take is one continuous recording.

---

## Alternative: full walkthrough with voice-over throughout (`aura-health-walkthrough-novoice.mp4`, 5:58)

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
