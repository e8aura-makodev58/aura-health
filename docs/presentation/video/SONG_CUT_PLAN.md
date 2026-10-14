# Song + voice-over cut plan (video with the ad song)

The song carries the self-explanatory opening and the close; a short voice-over carries the
middle, where the agent, safety, architecture and build reflection need explaining.
Song: [`../../submission/AURA_AD_SONG_v5.md`](../../submission/AURA_AD_SONG_v5.md) (sung version,
plus the instrumental version as a quiet bed under the voice). Video: the current silent cut,
`aura-health-walkthrough-novoice.mp4` (5:58), with your 8-second Miora intro and outro added.

Times below are **final-video times** (intro clip included). Song times assume about 96 BPM, inside the
prompt's 92–104 BPM; Suno picks the exact tempo, so after generating, move each cut to the
nearest phrase end (never speed the vocal up). Keep the finished video **at least 5:00** (it is
about 6:14).

## Cue sheet

| Final video | On screen | Audio |
|---|---|---|
| 0:00–0:08 | Miora intro | **Song 0:00–** (instrumental intro) |
| 0:08–1:07 | Slides 1–4: cover, challenge, problem, what AURA does | Song: Verse 1 → Pre-chorus → **Chorus** |
| 1:07–2:15 | Calm start, today's dose, medication answers | Song: Verse 2 → Pre-chorus → Chorus → guitar → **Bridge, ends ~2:15** ("…and where the story turns") |
| 2:15–2:33 | Appointment | **Voice A**, instrumental bed low (about −18 dB under voice) |
| 2:33–3:13 | Clinician + agent (first draft rejected → Ask again → checked answer) | **Voice B** |
| 3:13–3:36 | Simulated flu | **Voice C** |
| 3:36–4:03 | Safety example (masked) → safety panel → explanation card | **Voice D** |
| 4:03–4:57 | Slides 11–14: architecture, agent loop, safety precedence, trade-offs | **Voice E** |
| 4:57–5:22 | Slide 15: fit with the challenge | **Voice F** |
| 5:22–5:42 | Slide 16: how we built it | **Voice G** |
| 5:42–6:14 | Slides 17–18: impact, close; Miora outro | **Song: Final chorus → Outro** ("…room for your day"); hold the last frame or fade if the song runs ~3 s longer |

Mixing notes: fade the song down over ~1 s into Voice A and up over ~1 s after Voice G; leave a
beat of silence before the final chorus. Captions already on screen stay as they are.

## Voice-over script (about 450 words, ~150 words a minute)

**A · Appointment (2:15–2:33, ~18 s)**
> Before a visit, everything is in one place: what changed and when, and the skipped dose with
> its reason, ready to discuss with the doctor or pharmacist. Nothing is sent automatically. It
> stays *Not sent* until the patient decides.

**B · Clinician and agent (2:33–3:13, ~40 s)**
> If the patient shares, their clinician sees what changed and when, with exact values and
> sources, and can ask. Here AURA works as an agent: it decides which signals, tools and dates to
> read, then drafts an answer where every statement cites its source. A separate check reviews
> each statement. This time the first draft didn't pass, and AURA said so. Asked again, the
> answer passed, and *How AURA looked* shows exactly what it read. It can only read; it never
> changes the record or the treatment.

**C · Something changes (3:13–3:36, ~23 s)**
> Now a flu, simulated over three days. AURA notices resting heart rate is higher than in the
> person's recent records, and says exactly that: a recent change, not a change from their usual.
> It also offers a small, optional idea for today, never about medication.

**D · Safety first (3:36–4:03, ~27 s)**
> Anything a patient types is safety-checked first. Here the example message is masked. When
> there's a concern, fixed safety resources take over the screen and the AI steps back. The
> patient can't dismiss them, and the clinician sees the same state when they open the record.
> This prototype doesn't send alerts; who is told, and how fast, is for the care team to decide.

**E · How it's built (4:03–4:57, ~54 s)**
> Our rule: signals propose, rules decide, AI words it. A Python application owns all the state.
> Deterministic engines keep the personal baselines and the safety state; the AI never does.
> Medication information is curated, and AI only matches a question to an approved topic. The
> agent investigates with read-only, patient-scoped tools, within loop budgets: eight model
> steps, twenty-four tool calls, ninety seconds. Every answer passes number, date and citation
> checks, an independent verifier, and a final recheck of the safety state. Safety has the final
> say: a detector can never lower the safety state, and safety resources are shown
> without any AI model. The demo runs on synthetic data; a hospital would run the model on its own infrastructure.

**F · Fit with the challenge (4:57–5:22, ~25 s)**
> Against the challenge: medication understanding, adherence with reasons, health tracking,
> refill and review dates, and appointment preparation are in the demo. Push reminders,
> screenings and pharmacist-reviewed content come next. One choice is deliberate: AURA describes
> changes; it doesn't predict relapse or give medication advice.

**G · How we built it (5:22–5:42, ~20 s)**
> We built the safety and baseline core first, then the agent, then the experience, using AI
> development tools including Tencent's CodeBuddy and Miora, from written specs, with every change
> reviewed and tested. Our tip: write down what must never change before asking an AI to build
> anything.

Then the song takes over for the final chorus and the sung close: *"Room for your day, room
for your own way, Aura Health, room for your day."*

## What Claude can do once the audio exists

Given the Suno sung track, the instrumental track and your voice recording (one file, or one per
section A–G): place the cuts on phrase ends, mix the instrumental bed under the voice, add the
intro/outro clips, and export the final MP4, checking that it stays between 5 and 8 minutes.
