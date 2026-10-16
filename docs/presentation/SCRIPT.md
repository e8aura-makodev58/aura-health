# AURA Health — presentation and video script (v4, patient-first)

Status: v4 (2026-10-13, Claude); video note updated 2026-10-14: v3 order (matches the in-app guided story); scene 8 updated for the paced, masked safety example and what the clinician sees. v3 reordered v2 to put the flu after the clinician scene. Replaces v1 (clinician-first,
written before the patient companion existed). Target **7:00** for the live pitch (scene times below are pitch times, not video times), about 950
spoken words. This script drives the deck (also the required architecture PPT) and its speaker
notes, the live pitch, and the in-app "Play the 3-minute story" tour (same scene order).

Demo record: synthetic patient B (slow sleep drift, lower activity, Rough check-ins), patient
view unless stated. Rules for every take: synthetic data only; AI text is whatever the live run
produces, never edited; if the AI falls back, say so; no clinical-effectiveness claims.


> **Submission video (2026-10-14):** the video no longer uses this full script. It is a 3-minute
> first half with a shorter voice-over, then a live landscape demo under the song; text and
> timings in [`video/SONG_CUT_PLAN.md`](video/SONG_CUT_PLAN.md), on-screen times in
> [`video/VOICEOVER.md`](video/VOICEOVER.md). This script remains the live pitch and the source of
> the deck's speaker notes.

---

### 1 · The challenge — 0:00–0:25 (live pitch)
**Slide:** cover · "AURA Health — a calm companion between doctor visits" · Healthcare track badge.
> "We chose the Healthcare track's Challenge Statement 2, *AI Healthier Every Day*, Scenario 1:
> mental health maintenance for working adults on antidepressants. This is AURA Health."

### 2 · The problem — 0:25–0:55 (live pitch)
**Slide:** three short lines.
> "Staying well on an antidepressant happens mostly between appointments. A dose gets missed,
> sleep drifts later, a flu knocks you out for a few days. Most apps ask you to log your mood
> every evening, which is hard when you're tired or low. And when the appointment comes, it's
> all pieced together from memory."

### 3 · A calm start — 0:55–1:35 (live pitch)
**Screen:** landing → *Play the 3-minute story* → *Start* (the in-app guided story; each step highlights one thing and AURA does the tapping) → "Take a breath" → summary.
> "AURA starts with a breath, not a dashboard. Then one short summary, written by AI from facts
> the system has checked: sleep time later than usual since late February, and how the person
> has been checking in. It quietly reads everyday wearable data and compares it with *this
> person's* usual, not a population average."

### 4 · My medication, my day — 1:35–2:35 (live pitch)
**Screen:** *Today's dose* → tap *Skipped* → "What got in the way?" → *Side effects*.
Then *My medication* → *What if I miss a dose?*
> "Every morning there's one tap: taken, not yet, or skipped. If it's skipped, AURA asks what
> got in the way, because that's what's worth bringing to a doctor. *My medication* explains the
> person's own prescription in plain words: what it's for, how it's usually taken, what patient
> leaflets say about a missed dose. These answers come from approved information, not made up by AI, and
> they always point back to the pharmacist."
**Then type in *Ask a question*:** "Can I take ibuprofen with it?"
> "And when AURA can't answer, it says so: *I'm not able to identify that medication, please
> check with your pharmacist.* Exactly what the challenge asks for."

### 5 · Ready for the appointment — 2:35–3:05 (live pitch)
**Screen:** *Prepare for my appointment* → missed doses → *Not sent*.
> "Before the visit, everything is in one place: what changed, when, and the missed dose with
> its reason, ready to discuss with the doctor or pharmacist. Nothing is sent automatically.
> It stays *Not sent* until the patient decides."

### 6 · What the clinician sees — the agent at work — 3:05–4:10 (live pitch)
**Screen:** *Clinician* → assessment cards → *Ask about this record*:
"When did sleep timing change, and was anything reported around then?"
> "If the patient shares, their clinician sees what changed and when, with exact values and
> sources. And the clinician can ask. Here AURA works as an agent: it decides which signals,
> tools and dates to look at, reads the record, and drafts an answer where every statement cites
> its source. A second, independent check then reviews each statement and removes anything
> unsupported. *How AURA looked* shows exactly what it did. It can only read; it never changes
> the record or the treatment."
**If it falls back:**
> "This time the draft didn't pass the checks, so AURA shows the related facts and says why."

### 7 · Something changes — 4:10–4:50 (live pitch)
**Screen:** guided story step 9 → simulated flu → the patient home with the new summary and a small idea for today.
> "Now a flu, simulated over three days. AURA notices resting heart rate is higher than in the
> person's *recent* records, and says exactly that: a recent change, not a change from their
> usual. And when a change shows up, it offers a small idea for today: a short walk, a message
> to someone you trust, or planning a session. Optional, never about medication."

### 8 · Safety first — 4:50–5:15 (live pitch)
**Screen:** finish card → *Show the safety example* → the note box opens with *A worrying message* (masked on screen) → *Send to AURA* → safety panel → the card explains, with *Reset the demo*.
> "Anything a patient types is safety-checked first. If there's a concern, fixed safety
> resources take over the screen and the AI steps back. Those messages are never AI-written,
> and the patient can't dismiss them. The clinician sees the same safety state when they open
> the record. This prototype doesn't send alerts: who is told, and how fast, is for the care
> team to decide. The same applies to medication questions: asking to double a dose goes to
> safety, not to an answer."

### 9 · How it's built — 5:15–6:00 (live pitch)
**Slides:** architecture overview · agent loop · safety precedence (`diagrams/`).
> "Our rule: signals propose, rules decide, AI words it. Deterministic engines own the personal
> baselines and the safety state. Medication information is curated; AI only matches a question
> to an approved topic. The clinician agent investigates with read-only tools, and every answer
> passes number, date and citation checks plus an independent verifier. In this demo the model
> runs on synthetic data only; a hospital would run it on its own private infrastructure. And the
> patient decides what their clinician sees: an agreed minimum, plus anything they choose to share,
> enforced on the server, so the agent says 'not shared, ask the patient' instead of guessing."

### 10 · Fit with the challenge — 6:00–6:25 (live pitch)
**Slide:** six features: built / partial / next (from `../submission/CHALLENGE_MAPPING.md`).
> "Against the challenge: medication understanding, adherence with barriers, health tracking,
> follow-up dates for refills and medication reviews, and appointment preparation are in the
> demo. Push reminders, screenings and pharmacist-reviewed content come next. One choice is deliberate: AURA describes changes; it
> doesn't predict relapse or give medication advice."

### 11 · How we built it — 6:25–6:45 (live pitch)
**Slide:** how we built it (core first, AI development tools, reviews and tests).
> "We built the safety and personal-baseline core first, then the agent, then the experience,
> using AI development tools including Tencent's CodeBuddy and Miora, working from written specs,
> with every change reviewed and tested. Our tip: write down what must never change before asking
> an AI to build anything."

### 12 · Impact and close — 6:45–7:05 (live pitch)
**Slide:** pilot metrics (labelled as targets) · closing line.
> "In a pilot we'd measure missed doses with a recorded reason, preparation time before visits,
> and how many appointments start with a prepared note. AURA Health: a calm companion between
> doctor visits, so both sides start the conversation on the same page."

---

## Production notes

- **Order (matches the in-app guided story):** landing → patient (summary, dose, medication) →
  appointment → clinician + Q&A → flu → safety → slides. Reset the session first (Demo guide → *Reset this synthetic session*).
  Do the safety scene last: it changes the session's safety state.
- **AI allowance:** 30 calls/minute, 300/hour, shared. One take ≈ 25–45 calls.
- **Live model:** OpenAI gpt-6-luna, reasoning medium (operator setting). An agent answer takes
  about a minute; the video trims the wait.
- **Video:** see the note at the top: first half with voice-over (`video/SONG_CUT_PLAN.md`), second half a live landscape take under the song. The user records the voice-over; Claude records and assembles the picture.
- **Tour:** the in-app "Play the 3-minute story" follows scenes 3–8 in the same order; the video
  records that guided story itself.

---

## Q&A talking points

**"Why OpenAI and not a Tencent model?"** (the model name shows in the agent light's tooltip and the
admin settings; keep it visible: being open about the model is part of responsible AI)

> "AURA is model-agnostic by design: the model is a setting, because a hospital will run its own
> approved model, on-premises or in its private cloud. We built it with CodeBuddy, designed it with
> Miora and host it on Tencent Cloud Lighthouse. We tested Tencent's Hy4 and Kimi K3 through TokenHub
> against the same safety and grounding checks. For the demo we use the model that currently passes
> all of them fastest. Switching to a Tencent model is a settings change, once its answers pass those
> checks."

Facts behind it (2026-10-16, see HANDOVER): Hy4 preview tagged everyday activities about as well as
gpt-6-luna (34 vs 36 of 40 notes) but did not work with the agent's tool loop without prompt changes;
Kimi K3 called tools correctly but was too slow for the agent's time limit. The live site runs on
Tencent Cloud Lighthouse (Singapore), shown in the "AURA agent live" light.
