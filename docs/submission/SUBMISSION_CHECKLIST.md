# AURA Health · submission checklist and copy-paste text

One page for submitting the **TENCENT CLOUD HACKATHON SINGAPORE 2026: Project Submission** form.
Work top to bottom: tick the checklist, then copy each field's text from the boxes below.
Deadline recorded: **16 Oct 2026**; confirm the organiser's exact closing time and timezone.
Prepared 2026-10-14 against `main` (see the last section for the build and checks).

---

## 1 · Checklist

### Before you open the form
- [ ] Signed in with the team's Google account (its name, email and photo are recorded with uploads).
- [ ] Video recorded with voice-over and intro/outro, uploaded, link opens in a signed-out browser.
- [ ] Video length is **5–8 minutes** (combined draft is 6:07: 3:26 voice-over half + 2:40 landscape demo with the song; with intro/outro about 6:23).
- [ ] You have looked through the three upload files below and are happy with them.

### Fields
| # | Field | Required | What to enter | Ready? |
|---|---|---|---|---|
| 1 | Project Title | Yes | Text in box 2.1 | [ ] |
| 2 | Short Blurb (under 10 words) | Yes | Text in box 2.2 (7 words) | [ ] |
| 3 | Project Description | Yes | Text in box 2.3 | [ ] |
| 4 | Cover Image (16:9, max 1 MB) | Yes | Upload `docs/submission/assets/aura-cover-v2.jpg` (1672×941, 0.38 MB) | [ ] |
| 5 | Project Web Link | Yes | Box 2.4 | [ ] |
| 6 | Demo Video Link (5–8 min) | Yes | Your uploaded video's link (box 2.5) | [ ] |
| 7 | WorkBuddy/CodeBuddy Conversation History (chat + ≥ 3 screenshots, one file, max 10 MB) | Yes | Upload `docs/submission/assets/development-history.pdf` (27 pages, 3.6 MB: CodeBuddy transcript + 8 screenshots) | [ ] |
| 8 | Architecture Diagram PPT (one file, max 10 MB) | Yes | Upload `docs/submission/assets/aura-health-deck.pptx` (18 slides, 0.69 MB) | [ ] |
| 9 | Source Code (GitHub URL) | Yes | Box 2.6 (public, checked signed-out) | [ ] |
| 10 | Social Media Post Link | Bonus | Box 2.7, only if you publish a post | [ ] |

### Upload notes
- **Cover:** the original PNGs are 1.66 MB and 1.8 MB, over the 1 MB limit; the JPEG has the same resolution. If the live form accepts larger files, `Aura Health Wellness Dashboard Devices.png` is the original.
- **Conversation history:** the form asks for one file with chat history *and* at least 3 screenshots, so the PDF combines both. It does not require PDF; it is simply the format that holds both. Before uploading, glance at the Miora screenshots (your bookmarks bar is visible) and CodeBuddy screenshot 01 (the Tencent guide's file name is visible in the file list).
- **Deck:** text is in Nunito; install it (free, Google Fonts) on any computer that presents the deck. Slides 11–13 are native diagrams with arrows attached to the boxes.

### After submitting
- [ ] Screenshot or save the confirmation.
- [ ] Keep the live site running until judging ends: https://aura-health.makodev58.com
- [ ] Do not reset the live model settings (currently OpenAI gpt-6-luna, reasoning medium).

---

## 2 · Copy-paste text

Copy only what is inside each box.

### 2.1 Project Title
```
AURA Health
```

### 2.2 Short Blurb
```
Personal health patterns, clearer conversations between appointments.
```

### 2.3 Project Description
```
Project Overview: Target Scenarios, Users, and Value Proposition

Healthcare track (NTU Lee Kong Chian School of Medicine), Challenge Statement 2 "AI Healthier Every Day", Scenario 1: Mental Health Maintenance for Working Adults on Antidepressants.

AURA Health is a calm, wearable-first companion that keeps the context between doctor visits for adults aged 25–60 on stable, clinician-managed antidepressant maintenance. The patient sees a calm home: a breath, one short AI-written summary from checked facts, today's dose in one tap (with "what got in the way?" when a dose is skipped), plain answers about their own medication, upcoming review and refill dates, and an optional small idea for the day. The clinician they choose to share with sees what changed and when, with exact values and sources.

The differentiator is a bounded record-investigation agent, not an open chatbot. A clinician asks, for example, "When did sleep timing change, and was anything reported around then?" AURA-Agent decides which tools, signals and date windows to read, drafts an answer in which every statement cites its source, and a separate verification step checks each statement before it is shown. "How AURA looked" shows exactly what it read. The agent can only read; it never changes the record or the treatment.

Real World Scenario Insights: Pain Points, Audience, and Core Problem

Staying well on an antidepressant happens mostly between appointments. A dose gets missed, sleep drifts later, a flu knocks someone out for a few days. Most apps ask people to log their mood every evening, which is hard when they are tired or low, and at the appointment the weeks in between are pieced together from memory. Raw wearable readings, check-ins and medication records are hard to relate in time; a short illness can explain some changes, while a slowly adapting baseline can hide a longer shift.

These pain points shaped our design and synthetic scenarios; they are design hypotheses, not findings from a patient study.

Against the challenge, AURA covers medication understanding (curated information about the person's own prescription, with honest "please check with your pharmacist" when it cannot answer), medication management and adherence support (one tap a day, reasons for missed doses carried to the visit), health tracking against the person's own baseline and recent pattern, preventive dates (medication review and refill), and appointment preparation (a visit note that is not sent until the patient decides). Push reminders, screenings and vaccinations are not built yet. The scenario mentions flagging early signs of relapse; AURA deliberately stops at describing changes the patient can choose to bring to their clinician, because relapse prediction and treatment advice need clinical validation and sponsor governance.

Comprehensive Solution Design: Business, Architecture, and Prompts

Our rule is: signals propose, rules decide, AI words it. A Python/FastAPI application owns all state. Two deterministic engines sit at its core: a longitudinal engine with a governed personal baseline and a recent rolling reference, and a safety engine with explicit states that fails closed. Anything a patient types is safety-checked first; if there is a concern, fixed safety resources take over the screen, the AI steps back, and those messages are never AI-written. The patient cannot dismiss them, and the clinician sees the same safety state when they open the record. This prototype does not send alerts; who is told, and how fast, is for the care team to decide. Events, decisions and audits are stored through repository interfaces (SQLite for the demo).

Prompts drive generation through five versioned AURA-Agent skills: clinician briefing, record Q&A, patient recap, visit preparation and question ranking. Each prompt defines the goal, the permitted evidence, the read-only tools, a strict output schema and plain-language rules. In Q&A the model chooses retrieval and descriptive-analysis tools and their windows, then composes claims from the returned facts. Deterministic checks enforce source references, numbers, dates and allowed claims; a separate verifier call checks support; the current safety state is rechecked before anything is shown. If a draft fails, AURA shows related facts from the record and says so. Medication answers come from a curated catalogue awaiting pharmacist review; the model may only match a typed question to an approved topic, never write medication instructions.

The model gateway is provider-configurable (OpenAI, DeepSeek, OpenRouter, Tencent); an operator chooses the model and reasoning level and can list each provider's available models. The demo runs on synthetic data only. A separate simulation plane turns requests such as "a three-day flu" into seeded synthetic observations; only observable events enter the application, and hidden scenario truth stays outside product decisions. A guided three-minute story in the app walks a visitor through one person's day, the clinician's view, a flu and the safety path. Institution-hosted, on-premises or private-cloud models are an intended future deployment, not validated today.

Business Value: Engineering Evidence and Intended Impact

The intended value is less reporting burden for patients and a clearer, evidence-linked starting point for each appointment. We have not measured clinical outcomes, consultation time savings or financial return, and do not claim them.

Defined impact for a pilot (metrics to measure with the sponsor; targets to be agreed, not results): (1) missed doses with a recorded reason; (2) clinician preparation time to answer "what changed and when" before a visit; (3) share of appointments that start with a patient-prepared note; (4) share of AI answers passing source checks, and clinician-rated usefulness; (5) every safety-relevant input reaching the deterministic safety path first.

Engineering evidence: the current build passes 334 automated Python tests (14 October 2026, commit 4cf8c40) covering safety policy, longitudinal invariants, application transactions, source grounding, tool isolation and patient/clinician presentation, plus browser tests of the patient companion, guided story, settings and safety display. Six synthetic scenarios cover physical illness, slow drift, illness plus an independent change, an explained persistent shift, a wearable gap and return, and a safety handoff. In a small live check on 13 October 2026, the guided story's clinician question produced a checked, cited answer in 5 of 5 runs on the configured model (OpenAI gpt-6-luna, medium reasoning); answers can still fall back, and the demo shows that honestly.

AURA does not diagnose depression, predict relapse, determine suicide risk, prescribe or change treatment, provide psychotherapy, or operate as an emergency monitoring service. The demo uses synthetic data and engineering parameters and does not claim clinical validation. Next: consented real wearables, push reminders and screenings, pharmacist-reviewed content, institutional identity and privacy controls, and private hosting.
```

### 2.4 Project Web Link
```
https://aura-health.makodev58.com
```

### 2.5 Demo Video Link
```
PASTE YOUR VIDEO LINK HERE
```

### 2.6 Source Code
```
https://github.com/e8aura-makodev58/aura-health
```

### 2.7 Social Media Post Link (bonus, optional)
Only if you publish a post. Suggested caption:
```
AURA Health: a calm companion between doctor visits for people on long-term antidepressants. A bounded AI agent that reads, cites and checks; safety rules that always come first. Built for the Tencent Cloud Hackathon Singapore 2026. #WorkBuddy #CodeBuddy #Miora #TencentCloudHackathon
```

---

## 3 · What was checked (2026-10-14)

- Live site: loads for signed-out visitors (HTTP 200); guided story, safety example and Reset tested on the live site.
- GitHub: public; repo page, raw files and the deck open signed-out (HTTP 200). No `.env`, databases, keys, the Tencent ADP guide or the raw CodeBuddy export are in the repository.
- Tests: 334 Python tests pass on `main` (14 October 2026, commit 4cf8c40). Browser suites pass except `redesign.cjs` (a pre-existing layout check) and the older non-hosted `milestone6.cjs` (same 9 failures as before this work).
- Files: cover 383,483 bytes; history PDF 3,630,810 bytes; deck 687,993 bytes — all within limits.
- Not yet done: video link; your approval of the three files and this text.
