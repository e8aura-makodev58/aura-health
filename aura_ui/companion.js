/* Patient companion UI — PATIENT_COMPANION_SPEC.md §4.
   Presentation only. Builds against the §3 API contract with a mock
   fallback until Codex's GET /companion endpoint lands.
   Safety state always takes priority (spec §1.4). */
"use strict";

const companionMock = {
  safety_normal: true,
  medication: {
    name: "Sertraline", schedule: "50 mg, once each morning",
    known: true,
    purpose: "Sertraline belongs to a group of medicines called SSRIs. It is used to treat depression and anxiety. It can take a few weeks to start working. Development content — needs pharmacist review.",
    how_to_take: "Take it once each morning with water, with or without food. Swallow whole. Development content — needs pharmacist review.",
    missed_dose: "If you forget a dose, take it as soon as you remember. If it is close to your next dose, skip the missed one. Do not take two doses together. Development content — needs pharmacist review.",
    side_effects: "Common side effects may include feeling sick, dry mouth, or changes in sleep. These often settle. Tell your doctor if they persist. Development content — needs pharmacist review.",
    alcohol: "It is best to avoid alcohol while taking this medicine. If you are unsure, check with your pharmacist or doctor. Development content — needs pharmacist review.",
    topics: [
      {id:"purpose", label:"What is it for?"},
      {id:"how_to_take", label:"How do I take it?"},
      {id:"missed_dose", label:"What if I miss a dose?"},
      {id:"side_effects", label:"Common side effects"},
      {id:"alcohol", label:"Alcohol"}
    ],
    content_status: "Development content — needs pharmacist review"
  },
  dose_today: {scheduled_time: "2026-03-11T08:00:00+00:00", status: null},
  adherence: {window_days: 7, taken_days: 6, recorded_days: 7,
    missed_reasons: [{reason: "SIDE_EFFECTS", label: "Side effects", count: 1}]},
  coming_up: [
    {kind: "MEDICATION_REVIEW", date: "2026-03-24", label: "Medication review with your doctor"},
    {kind: "REFILL", date: "2026-03-19", label: "Refill estimated"},
    {kind: "APPOINTMENT", date: "2026-03-24", label: "Next appointment"}
  ],
  suggestions: {
    because: "You've been moving less than your usual since early March.",
    options: [
      {id:"short_walk", label:"A short walk outside"},
      {id:"message_someone", label:"Message someone you trust"},
      {id:"plan_session", label:"Plan a session with your therapist or counsellor"}
    ]
  }
};

const comingUpIcons = {MEDICATION_REVIEW:"▤", REFILL:"○", APPOINTMENT:"→"};

function renderCompanion(data) {
  const root = document.getElementById("companion-cards");
  if (!data || !data.safety_normal) { root.hidden = true; return; }
  root.hidden = false;

  // Today's dose
  const doseCard = document.getElementById("dose-card");
  doseCard.hidden = !data.medication;
  if (data.medication) {
    document.getElementById("dose-detail").textContent =
      `${data.medication.name} · ${data.medication.schedule}`;
    const status = data.dose_today?.status;
    const btns = doseCard.querySelectorAll(".dose-btn");
    btns.forEach(btn => btn.setAttribute("aria-pressed",
      String(btn.dataset.dose === status)));
    document.getElementById("dose-reason").hidden = status !== "MISSED";
    document.getElementById("dose-saved").textContent =
      status ? `Recorded: ${status === "ACKNOWLEDGED" ? "Taken" : status === "MISSED" ? "Skipped" : "Not yet"}` : "";
  }

  // My medication
  const medCard = document.getElementById("medication-card");
  medCard.hidden = !data.medication;
  if (data.medication) {
    const med = data.medication;
    document.getElementById("medication-name").textContent = med.name;
    document.getElementById("medication-schedule").textContent = med.schedule;
    document.getElementById("medication-disclaimer").textContent = med.content_status || "";
    const chips = document.getElementById("topic-chips");
    chips.replaceChildren();
    if (med.known === false) {
      const abstain = document.createElement("p");
      abstain.className = "medication-answer";
      abstain.style.display = "block";
      abstain.textContent = "I'm not able to identify that medication, please check with your pharmacist.";
      medCard.append(abstain);
    } else if (med.topics) {
      for (const topic of med.topics) {
        const chip = document.createElement("button");
        chip.className = "topic-chip";
        chip.dataset.topicId = topic.id;
        chip.textContent = topic.label;
        chip.addEventListener("click", () => medicationTopic(topic.id));
        chips.append(chip);
      }
    }
  }

  // Coming up
  const comingCard = document.getElementById("coming-up-card");
  comingCard.hidden = !data.coming_up?.length;
  if (data.coming_up?.length) {
    const list = document.getElementById("coming-up-list");
    list.replaceChildren();
    for (const item of data.coming_up) {
      const li = document.createElement("li");
      const icon = document.createElement("span");
      icon.className = "coming-up-icon";
      icon.textContent = comingUpIcons[item.kind] || "•";
      icon.setAttribute("aria-hidden", "true");
      const dateSpan = document.createElement("span");
      dateSpan.className = "coming-up-date";
      dateSpan.textContent = companionDateLabel(item.date);
      const labelSpan = document.createElement("span");
      labelSpan.className = "coming-up-label";
      labelSpan.textContent = item.label;
      li.append(icon, dateSpan, labelSpan);
      list.append(li);
    }
  }

  // Suggestions
  const sugCard = document.getElementById("suggestion-card");
  sugCard.hidden = !data.suggestions;
  if (data.suggestions) {
    document.getElementById("suggestion-reason").textContent = data.suggestions.because;
    const opts = document.getElementById("suggestion-options");
    opts.replaceChildren();
    for (const opt of data.suggestions.options) {
      const chip = document.createElement("button");
      chip.className = "suggestion-chip";
      chip.dataset.suggestionId = opt.id;
      chip.textContent = opt.label;
      const check = document.createElement("span");
      check.className = "suggestion-check";
      check.setAttribute("aria-hidden", "true");
      check.textContent = "✓";
      chip.append(check);
      chip.addEventListener("click", () => {
        chip.setAttribute("aria-pressed",
          String(chip.getAttribute("aria-pressed") !== "true"));
      });
      opts.append(chip);
    }
  }

  // Missed-dose items on the review page
  renderMissedDoses(data);
}

function companionDateLabel(iso) {
  try {
    return new Intl.DateTimeFormat("en-GB",
      {day:"numeric", month:"short", timeZone:"UTC"}).format(new Date(iso));
  } catch { return iso; }
}

let selectedTopic = null;
function medicationTopic(topicId) {
  const data = window.auraCompanionData;
  if (!data?.medication) return;
  selectedTopic = topicId;
  for (const chip of document.querySelectorAll(".topic-chip")) {
    chip.setAttribute("aria-pressed", String(chip.dataset.topicId === topicId));
  }
  const answerArea = document.getElementById("medication-answer");
  answerArea.hidden = false;
  document.getElementById("answer-text").textContent = data.medication[topicId] || "";
  document.getElementById("answer-source").textContent =
    "Approved medication information (development content)";
}

async function loadCompanion(patientId) {
  try {
    const response = await fetch(`/patients/${encodeURIComponent(patientId)}/companion`, {cache:"no-store"});
    if (response.ok) {
      const data = await response.json();
      window.auraCompanionData = data;
      renderCompanion(data);
      return;
    }
  } catch { /* endpoint not ready yet — use mock */ }
  // Mock fallback: synthetic data per spec §2
  window.auraCompanionData = companionMock;
  renderCompanion(companionMock);
}

function renderMissedDoses(data) {
  const section = document.getElementById("missed-dose-items");
  const adherence = data?.adherence;
  if (!adherence || adherence.taken_days >= adherence.recorded_days) {
    section.hidden = true;
    return;
  }
  const missedCount = adherence.recorded_days - adherence.taken_days;
  section.hidden = false;
  const reasons = adherence.missed_reasons || [];
  const reasonText = reasons.length
    ? reasons.map(r => `${r.count} — reason: ${r.label.toLowerCase()}`).join("; ")
    : "no reason recorded";
  document.getElementById("missed-dose-summary").textContent =
    `Missed doses in the last ${adherence.window_days} days: ${missedCount} — ${reasonText}. Worth discussing with your doctor or pharmacist.`;
  const list = document.getElementById("missed-dose-list");
  list.replaceChildren();
  for (const reason of reasons) {
    const li = document.createElement("li");
    li.textContent = `${reason.count} missed — ${reason.label}. Discuss with your doctor or pharmacist.`;
    list.append(li);
  }
}

// Dose recording buttons
document.addEventListener("click", async (event) => {
  const doseBtn = event.target.closest("[data-dose]");
  if (doseBtn) {
    const status = doseBtn.dataset.dose;
    const ctx = window.auraAgentContext?.() || {};
    const patientId = ctx.patientId;
    if (!patientId) return;
    // Show reason chips if MISSED
    document.getElementById("dose-reason").hidden = status !== "MISSED";
    // Update button states
    for (const btn of document.querySelectorAll(".dose-btn"))
      btn.setAttribute("aria-pressed", String(btn === doseBtn));
    document.getElementById("dose-saved").textContent =
      status === "ACKNOWLEDGED" ? "Recorded: Taken" :
      status === "MISSED" ? "Recorded: Skipped" : "Recorded: Not yet";
    // Send event
    try {
      const at = new Date().toISOString();
      await fetch(`/patients/${encodeURIComponent(patientId)}/events`, {
        method:"POST", headers:{"Content-Type":"application/json"},
        body: JSON.stringify({event_type:"MEDICATION_EVENT", occurred_at:at, source:"patient",
          payload:{scheduled_time:at, status}, correlation_id:window.auraUniqueId(),
          idempotency_key:window.auraUniqueId(), event_id:window.auraUniqueId()})
      });
    } catch { /* offline — state already reflected in UI */ }
    return;
  }
  const reasonBtn = event.target.closest("[data-reason]");
  if (reasonBtn) {
    const reason = reasonBtn.dataset.reason;
    for (const btn of document.querySelectorAll(".reason-chip"))
      btn.setAttribute("aria-pressed", String(btn === reasonBtn));
    const ctx = window.auraAgentContext?.() || {};
    const patientId = ctx.patientId;
    if (!patientId) return;
    try {
      const at = new Date().toISOString();
      await fetch(`/patients/${encodeURIComponent(patientId)}/events`, {
        method:"POST", headers:{"Content-Type":"application/json"},
        body: JSON.stringify({event_type:"MEDICATION_EVENT", occurred_at:at, source:"patient",
          payload:{scheduled_time:at, status:"MISSED", reason}, correlation_id:window.auraUniqueId(),
          idempotency_key:window.auraUniqueId(), event_id:window.auraUniqueId()})
      });
    } catch { /* offline */ }
    return;
  }
});

// Medication ask
document.addEventListener("click", async (event) => {
  const askBtn = event.target.closest("#medication-ask-btn");
  if (!askBtn) return;
  const question = document.getElementById("medication-question").value.trim();
  if (!question) return;
  askBtn.disabled = true;
  const answerArea = document.getElementById("medication-answer");
  answerArea.hidden = false;
  try {
    const ctx = window.auraAgentContext?.() || {};
    const response = await fetch(`/patients/${encodeURIComponent(ctx.patientId)}/medication/ask`, {
      method:"POST", headers:{"Content-Type":"application/json"},
      body: JSON.stringify({run_id: window.auraUniqueId(), question})
    });
    if (response.ok) {
      const result = await response.json();
      document.getElementById("answer-text").textContent = result.answer;
      document.getElementById("answer-source").textContent = result.source_label || "";
    } else {
      throw new Error("endpoint not ready");
    }
  } catch {
    // Mock abstention: safety gate first, then topic classifier
    document.getElementById("answer-text").textContent =
      "I'm not able to answer that here, please check with your pharmacist or doctor.";
    document.getElementById("answer-source").textContent =
      "Development content — needs pharmacist review";
  } finally {
    askBtn.disabled = false;
  }
});

// Hook into the existing render cycle
document.addEventListener("aura-record-view", () => {
  const ctx = window.auraAgentContext?.();
  if (!ctx?.patientId || ctx.role !== "patient") {
    document.getElementById("companion-cards").hidden = true;
    return;
  }
  // Spec §1.4: hide companion cards when safety pathway is active
  const safetyActive = !document.getElementById("safety-panel").hidden;
  if (safetyActive) {
    document.getElementById("companion-cards").hidden = true;
    return;
  }
  loadCompanion(ctx.patientId);
});

// Also load when patient view first renders
window.addEventListener("load", () => {
  const checkReady = setInterval(() => {
    const ctx = window.auraAgentContext?.();
    if (ctx?.patientId && ctx.role === "patient" && ctx.record) {
      clearInterval(checkReady);
      loadCompanion(ctx.patientId);
    }
  }, 500);
});
