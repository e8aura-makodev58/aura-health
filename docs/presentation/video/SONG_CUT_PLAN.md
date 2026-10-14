# Song + voice-over cut plan (v2: voice-over first, song over the landscape demo)

User direction 2026-10-14: the **first half** is the 3-minute walkthrough with **voice-over**; the
**second half** is a **full live demo of the app on a PC in landscape**, carried by the song.
This replaces the earlier plan (song–voice–song); the total stays inside the form's 5–8 minutes.

| File (in `docs/presentation/video/`, not in git) | Length | What it is |
|---|---|---|
| `aura-health-part1-voiceover-novoice.mp4` | 3:00 | First half: slides + phone story highlights + agent + flu + safety + architecture + challenge fit + **How we built it** |
| `aura-health-landscape-demo-novoice.mp4` | 2:40 | Second half: one continuous, uncut live take of the guided story at 1920×1080, through the safety example (the agent's answer passed its checks first time in this take) |
| `aura-health-combined-draft-novoice.mp4` | 5:40 | The two halves joined, silent; add the 8-s Miora intro and outro → **about 5:56** |

Built by `tools/assemble_short.py` (with `FIRST_HALF=1`) and `tools/assemble_landscape.py`; the
landscape take comes from `tools/record_tour.cjs <url> <dir> deskfull`.

## Cue sheet (final-video times, intro clip included)

| Final video | On screen | Audio |
|---|---|---|
| 0:00–0:08 | Miora intro | Soft instrumental (optional), or silence |
| 0:08–3:08 | First half (part 1) | **Your voice-over 1–10** below; optional instrumental bed very low |
| 3:08–5:48 | Landscape live demo | **Song (v5)** from the start; the guided story's own cards explain each step |
| 5:48–5:56 | Miora outro | Song outro ("…Aura Health, room for your day"); hold or fade to fit |

The song runs about 2:37–2:57 (92–104 BPM); the landscape demo plus the outro clip is 2:48. If the
song is longer, hold the outro image; if shorter, let the last demo frame hold. Never speed the
vocal up. Keep the finished video between 5:00 and 8:00.

## Voice-over script for the first half (about 400 words)

**1 · Cover, problem, what AURA does (0:08–0:32, ~24 s)**
> This is AURA Health, for the Healthcare track. Staying well on an antidepressant happens mostly
> between appointments: a missed dose, sleep drifting later, a flu. Most apps ask you to log your
> mood every evening. AURA quietly reads everyday wearable data and compares it with this
> person's own usual.

**2 · A calm start (0:32–0:59, ~27 s)**
> It starts with a breath, not a dashboard. Then one short summary, written by AI from facts the
> system has checked: sleep later than usual since late February, and how the person has been
> checking in.

**3 · Medication (0:59–1:18, ~19 s)**
> One tap a day for the dose. If it's skipped, AURA asks what got in the way. Medication answers
> come from approved information, and when AURA can't answer, it says so and points to the
> pharmacist.

**4 · Appointment (1:18–1:27, ~9 s)**
> Before the visit, the skipped dose and its reason are ready to discuss. Nothing is sent until
> the patient decides.

**5 · The agent (1:27–1:53, ~26 s)**
> The clinician can ask. AURA's agent decides which records and dates to read, and drafts an
> answer where every statement cites its source. A separate check reviews each statement. Here
> the first draft failed, AURA said so, and the next one passed. It can only read.

**6 · Something changes (1:53–2:06, ~13 s)**
> A simulated flu: AURA describes what changed in this person's recent records, and offers a
> small, optional idea for today.

**7 · Safety first (2:06–2:23, ~17 s)**
> Anything a patient types is safety-checked first. If there's a concern, fixed safety resources
> take over and the AI steps back. The patient can't dismiss them. This prototype sends no alerts.

**8 · Architecture and agent loop (2:23–2:45, ~22 s)**
> Our rule: signals propose, rules decide, AI words it. Deterministic engines own the baselines
> and the safety state. The agent uses read-only tools within loop budgets, and every draft is
> grounded, verified and rechecked before it's shown.

**9 · Fit with the challenge (2:45–2:57, ~12 s)**
> Medication understanding, adherence, health tracking, follow-up dates and appointment
> preparation are in the demo. AURA describes changes; it doesn't predict relapse or give
> medication advice.

**10 · How we built it (2:57–3:08, ~11 s)**
> We built the core first, then the agent, then the experience, using CodeBuddy and Miora. Our
> tip: write down what must never change first.

Then the song starts with the landscape demo.

## What Claude can do once the audio exists

Given your voice recording (one file, or one per section 1–10) and the Suno sung track: place the
voice on the first half, start the song on the landscape demo, add the intro/outro clips, balance
levels, and export the final MP4, checking it stays between 5 and 8 minutes.
