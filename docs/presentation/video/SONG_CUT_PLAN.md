# Song + voice-over cut plan (v2: voice-over first, song over the landscape demo)

User direction 2026-10-14: the **first half** is the 3-minute walkthrough with **voice-over**; the
**second half** is a **full live demo of the app on a PC in landscape**, carried by the song.
This replaces the earlier plan (song–voice–song); the total stays inside the form's 5–8 minutes.

| File (in `docs/presentation/video/`, not in git) | Length | What it is |
|---|---|---|
| `aura-health-part1-voiceover-novoice.mp4` | 3:26 | First half: slides + phone story highlights + agent + flu + safety + architecture + challenge fit + **How we built it** |
| `aura-health-landscape-demo-novoice.mp4` | 2:40 | Second half: one continuous, uncut live take of the guided story at 1920×1080, through the safety example (the agent's answer passed its checks first time in this take) |
| `aura-health-combined-draft-novoice.mp4` | 6:07 | The two halves joined, silent; add the 8-s Miora intro and outro → **about 6:23** |

Built by `tools/assemble_short.py` (with `FIRST_HALF=1`) and `tools/assemble_landscape.py`; the
landscape take comes from `tools/record_tour.cjs <url> <dir> deskfull`.

## Cue sheet (final-video times, intro clip included)

| Final video | On screen | Audio |
|---|---|---|
| 0:00–0:08 | Miora intro | Soft instrumental (optional), or silence |
| 0:08–3:34 | First half (part 1) | **Your voice-over 1–10** below; optional instrumental bed very low |
| 3:34–6:15 | Landscape live demo | **Song (v5)** from the start; the guided story's own cards explain each step |
| 6:15–6:23 | Miora outro | Song outro ("…Aura Health, room for your day"); hold or fade to fit |

The song runs about 2:37–2:57 (92–104 BPM); the landscape demo plus the outro clip is 2:48. If the
song is longer, hold the outro image; if shorter, let the last demo frame hold. Never speed the
vocal up. Keep the finished video between 5:00 and 8:00.

## Voice-over script for the first half (about 320 words)

Paced for a relaxed read: about 110 words a minute, with a breath at each cut. Start each section
about a second after its picture appears; it's fine to finish a little early.

**1 · Cover, problem, what AURA does (0:08–0:35, ~27 s)**
> This is AURA Health, for the Healthcare track. Staying well on an antidepressant happens
> between appointments: a missed dose, later sleep, a flu. Most apps ask you to log your mood
> every evening. AURA quietly reads wearable data and compares it with your own usual.

**2 · A calm start (0:35–1:02, ~27 s)**
> It starts with a breath, not a dashboard. Then one short summary, written by AI from facts the
> system has checked: sleep later than usual since late February, and how the person has been
> checking in.

**3 · Medication (1:02–1:24, ~22 s)**
> One tap a day for the dose. If it's skipped, AURA asks what got in the way. Medication answers
> come from approved information, and when AURA can't answer, it says so and points to the
> pharmacist.

**4 · Appointment (1:24–1:37, ~13 s)**
> Before the visit, the skipped dose and its reason are ready to discuss. Nothing is sent until
> the patient decides.

**5 · The agent (1:37–2:06, ~29 s)**
> The clinician can ask. AURA's agent decides which records and dates to read, and drafts an
> answer where every statement cites its source. A separate check reviews each statement. Here
> the first draft failed, AURA said so, and the next one passed. It can only read.

**6 · Something changes (2:06–2:20, ~14 s)**
> A simulated flu: AURA describes what changed in this person's recent records, and offers a
> small, optional idea for today.

**7 · Safety first (2:20–2:39, ~19 s)**
> Anything a patient types is safety-checked first. If there's a concern, fixed safety resources
> take over and the AI steps back. The patient can't dismiss them. This prototype sends no alerts.

**8 · Architecture and agent loop (2:39–3:03, ~24 s)**
> Our rule: signals propose, rules decide, AI words it. Deterministic engines own the baselines
> and the safety state. The agent uses read-only tools within loop budgets, and every draft is
> grounded, verified and rechecked before it's shown.

**9 · Fit with the challenge (3:03–3:19, ~16 s)**
> Medication understanding, adherence, health tracking, follow-up dates and appointment
> preparation are in the demo. AURA describes changes; it doesn't predict relapse or give
> medication advice.

**10 · How we built it (3:19–3:34, ~15 s)**
> We built the core first, then the agent, then the experience, using CodeBuddy and Miora. Our
> tip: write down what must never change first.

Then the song starts with the landscape demo.

## What Claude can do once the audio exists

Given your voice recording (one file, or one per section 1–10) and the Suno sung track: place the
voice on the first half, start the song on the landscape demo, add the intro/outro clips, balance
levels, and export the final MP4, checking it stays between 5 and 8 minutes.
