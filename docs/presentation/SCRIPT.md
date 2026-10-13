# AURA Health — presentation and video script (draft v1)

Status: DRAFT for the user's approval, 2026-10-13, Claude. Target **7:00** (allowed 5–8 min),
about 900 spoken words at a calm pace. Once approved, this script drives (1) the slide deck,
(2) the screen recording and (3) the narrated video. Screenshots referenced are in
`screenshots/`; architecture diagrams come from Codex (`diagrams/`, pending).

Honesty rules for every take: synthetic data only; AI text is whatever the live run produces
(no staging, no editing); if an answer falls back, say so; no clinical-effectiveness claims.

---

### 1 · Title and chosen challenge — 0:00–0:25
**Slide:** cover image · "AURA Health — Context between appointments" · track badge.
**Say:**
> "We chose the Healthcare track's Challenge Statement 2, *AI Healthier Every Day*, Scenario 1:
> mental health maintenance for working adults on antidepressants. This is AURA Health."

### 2 · The problem — 0:25–1:00
**Slide:** three short lines with a simple illustration.
**Say:**
> "Between appointments, a lot happens that nobody can see. Sleep drifts later, activity drops,
> a flu comes and goes. Most apps ask the patient to log their mood every day, which is hard when
> you're tired or low. And when the appointment comes, both sides are piecing the weeks together
> from memory."

### 3 · What AURA does — 1:00–1:20
**Screen:** landing (`01-landing-desktop`).
**Say:**
> "AURA quietly reads everyday wearable data, compares it with the person's *own* usual, and turns
> it into two views: a calm one for the patient, and a clear 'what changed and when' for their
> clinician."

### 4 · The patient's day — 1:20–2:10
**Screen:** tap *See the patient's day* → breathing welcome (`03`) → home (`04`) → *See what changed* (`05`).
**Say:**
> "The patient starts with a breath, not a dashboard. Then one short summary in everyday words.
> This sentence is written by AURA's AI, but only from facts the system has checked, and it's
> tested before it's shown. No charts, no scores. If they want detail, it's one tap away. The one
> thing that's always on screen is this button: *I want to mention something*."

### 5 · A life event — 2:10–2:45
**Screen:** demo guide → *Simulate: flu 3 days* → patient home after (`08`).
**Say:**
> "Let's simulate three days of flu. AURA notices that resting heart rate is higher than in the
> person's *recent* records, and says exactly that: a recent change, not a change from their usual.
> That difference matters. A flu is short. A slow drift in sleep over weeks is something else, and
> AURA keeps both references so they don't get mixed up."

### 6 · The clinician view — 2:45–3:30
**Screen:** *Clinician* → assessment cards (`09`) → charts (`10`).
**Say:**
> "Now the clinician. The first screen answers one question: what changed, and when. Sleep about
> three and a half hours later since late February; activity about two thousand steps a day lower
> since early March. Every number is exact and every card links to its source. The charts show
> the person's usual as a dashed line, and the recent average moving away from it."

### 7 · The agent at work — 3:30–4:30
**Screen:** type the question live → answer with *How AURA looked* (`11`).
**Ask:** "When did sleep timing change, and was anything reported around then?"
**Say:**
> "Here's where AURA is an agent, not a chatbot. I ask a question. AURA decides what to look
> at: which signals, which tools, which dates. It reads the record, drafts an answer, and every
> statement cites its source. Then a second, independent check reviews each statement. Here it
> reviewed nine and removed one it couldn't support. You can see exactly what it did, right here:
> *How AURA looked*. And it can only read; it can never change the record or the treatment."
**If it falls back, say instead:**
> "This time the draft didn't pass the checks, so AURA shows the related recorded facts and tells
> you why. You can still see what it investigated."

### 8 · Ready for the appointment — 4:30–4:55
**Screen:** patient → *Prepare for my appointment* (`06`).
**Say:**
> "Before the visit, the patient chooses what to bring. Nothing is sent automatically. It says
> *Not sent* until the patient decides."

### 9 · Safety comes first — 4:55–5:20
**Screen:** *I want to mention something* (`07`) → safety example → safety panel (`12`).
**Say:**
> "Anything a patient writes goes through a safety check first. If there's a concern, a fixed
> safety message and resources take over the screen. These are never written by AI, and the AI
> assistant pauses."

### 10 · How it's built — 5:20–6:05
**Slides:** architecture overview, agent loop, trust boundaries (Codex diagrams).
**Say:**
> "Our rule is: signals propose, rules decide, the AI words it. Deterministic engines own the
> personal baselines and the safety state. The AI agent investigates with read-only tools, and
> every answer passes number, date and citation checks plus an independent verifier. The model
> is configurable and runs only on synthetic data in this demo; a hospital would run it on its own
> private infrastructure."

### 11 · Fit with the challenge — 6:05–6:30
**Slide:** built / roadmap / deliberately different (from `../submission/CHALLENGE_MAPPING.md`).
**Say:**
> "Against the challenge: health tracking, appointment preparation and strict boundaries are
> built. Medication explanations, reminders and preventive nudges are next. And one choice is
> deliberate: AURA describes changes; it doesn't predict relapse or give advice. That needs
> clinical validation, and it's the sponsor's call."

### 12 · How we built it — 6:30–6:50
**Slide:** CodeBuddy and Miora screenshots (genuine sessions only).
**Say:**
> "We built the deterministic core first, then the agent, then the experience. CodeBuddy
> redesigned the interface from a written brief with clear boundaries; Miora created the artwork.
> Our tip: write down what must never change before you ask an AI to redesign anything."

### 13 · Impact and close — 6:50–7:10
**Slide:** pilot metrics (labelled as targets) + roadmap + closing line.
**Say:**
> "In a pilot we'd measure patient effort, clinician preparation time, and how many appointments
> start with a prepared note. AURA Health: context between appointments, so both sides start the
> conversation on the same page."

---

## Production notes

- **Order on screen:** landing → patient → flu → clinician → Q&A → appointment → safety → slides.
  Reset the demo session before the take ("Reset this synthetic session" in the demo guide).
- **AI allowance:** 30 calls/minute, 300/hour shared. One full take uses roughly 20–40 calls.
- **Video:** Claude can record the screen walkthrough following this script and assemble it with the
  slides; the voice-over needs a human (no voice tools here). Narration can be recorded separately
  and laid over the recording.
- **Open items:** cover image (CodeBuddy/Miora), diagrams (Codex), CodeBuddy/Miora session
  screenshots (user), final timing after a read-through.
