/* Patient companion UI — PATIENT_COMPANION_SPEC.md §4.
   Presentation only. Requires Codex's GET /companion endpoint.
   Safety state always takes priority (spec §1.4).
   On any error the cards are hidden; no built-in medication text is shown. */
"use strict";

const comingUpIcons = {MEDICATION_REVIEW:"▤", REFILL:"○", APPOINTMENT:"→"};
// Ideas chosen today stay ticked across re-renders; only the newest agent pick is applied.
const chosenIdeas = {patient: null, ids: new Set()};
let ideaTicket = 0;

function companionDateLabel(iso) {
  try {
    return new Intl.DateTimeFormat("en-GB",
      {day:"numeric", month:"short", timeZone:"UTC"}).format(new Date(iso));
  } catch { return iso; }
}

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
    for (const btn of doseCard.querySelectorAll(".dose-btn"))
      btn.setAttribute("aria-pressed", String(btn.dataset.dose === status));
    document.getElementById("dose-reason").hidden = status !== "MISSED";
    // Clear any stale "Recorded" text from a prior interaction
    document.getElementById("dose-saved").textContent = "";
    // Reset reason chip selection on re-render
    for (const chip of document.querySelectorAll(".reason-chip"))
      chip.setAttribute("aria-pressed", "false");
  }

  // My medication — topic chips built once; abstention is server-driven
  const medCard = document.getElementById("medication-card");
  medCard.hidden = !data.medication;
  if (data.medication) {
    const med = data.medication;
    document.getElementById("medication-name").textContent = med.name;
    document.getElementById("medication-schedule").textContent = med.schedule;
    document.getElementById("medication-disclaimer").textContent = med.content_status || "";
    const chips = document.getElementById("topic-chips");
    chips.replaceChildren();
    // Unknown medication: say so up front with the server's exact abstention line.
    let abstain = document.getElementById("medication-abstain");
    if (!abstain) { abstain = document.createElement("p"); abstain.id = "medication-abstain"; abstain.className = "medication-answer"; chips.before(abstain); }
    abstain.hidden = med.known !== false;
    abstain.textContent = med.known === false ? (med.abstain || "") : "";
    if (med.topics && med.known !== false) {
      for (const topic of med.topics) {
        const chip = document.createElement("button");
        chip.className = "topic-chip";
        chip.dataset.topicId = topic.id;
        chip.textContent = topic.label;
        chip.addEventListener("click", () => medicationTopic(topic.id));
        chips.append(chip);
      }
    }
    // Keep an answer across refreshes of the same patient (a typed question reloads the
    // record); clear it only when a different patient is shown.
    const shownFor = window.auraAgentContext?.()?.patientId;
    if (window.auraMedicationAnswerFor !== shownFor) document.getElementById("medication-answer").hidden = true;
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
    const patient = window.auraAgentContext?.()?.patientId || null;
    if (chosenIdeas.patient !== patient) { chosenIdeas.patient = patient; chosenIdeas.ids = new Set(); document.getElementById("suggestion-ack").hidden = true; }
    for (const row of data.chosen_today || []) chosenIdeas.ids.add(row.option_id);
    document.getElementById("suggestion-why").hidden = true;
    document.getElementById("suggestion-origin").hidden = true;
    buildSuggestionChips(data.suggestions.options);
    personalizeSuggestions();
  }

  // Missed-dose items on the review page
  renderMissedDoses(data);
  loadActivities();
}

function buildSuggestionChips(options) {
  const chosen = chosenIdeas.ids;
  const opts = document.getElementById("suggestion-options");
  opts.replaceChildren();
  for (const opt of options) {
    const chip = document.createElement("button");
    chip.className = "suggestion-chip";
    chip.dataset.suggestionId = opt.id;
    chip.textContent = opt.label;
    chip.setAttribute("aria-pressed", String(chosen.has(opt.id)));
    const check = document.createElement("span");
    check.className = "suggestion-check";
    check.setAttribute("aria-hidden", "true");
    check.textContent = "✓";
    chip.append(check);
    chip.addEventListener("click", () => chooseSuggestion(chip, opt));
    opts.append(chip);
  }
}

// The agent may re-pick today's ideas from the curated pool for this person (server-checked);
// the rule-based ideas stay on screen until then, and if it is unavailable.
async function personalizeSuggestions() {
  const ctx = window.auraAgentContext?.();
  if (!ctx?.patientId) return;
  const patient = ctx.patientId, ticket = ++ideaTicket;
  try {
    const response = await fetch(`/patients/${encodeURIComponent(patient)}/companion/suggestions/personalize`, {method:"POST"});
    if (!response.ok) return;
    const result = await response.json();
    if (!result.personalized || ticket !== ideaTicket || window.auraAgentContext?.()?.patientId !== patient) return;
    buildSuggestionChips(result.options);
    const why = document.getElementById("suggestion-why");
    why.textContent = result.why; why.hidden = false;
    document.getElementById("suggestion-origin").hidden = false;
  } catch { /* keep the rule-based ideas */ }
}

async function chooseSuggestion(chip, opt) {
  const ctx = window.auraAgentContext?.();
  if (!ctx?.patientId || chip.getAttribute("aria-pressed") === "true") return;
  const ack = document.getElementById("suggestion-ack");
  chip.disabled = true;
  try {
    const response = await fetch(`/patients/${encodeURIComponent(ctx.patientId)}/companion/suggestions/choose`, {
      method:"POST", headers:{"Content-Type":"application/json"}, body: JSON.stringify({option_id: opt.id})});
    if (!response.ok) throw new Error("Request failed");
    const result = await response.json();
    chip.setAttribute("aria-pressed", "true");
    chosenIdeas.ids.add(opt.id);
    ack.textContent = result.message; ack.hidden = false;
  } catch {
    ack.textContent = "That couldn't be saved just now. Please try again."; ack.hidden = false;
  } finally { chip.disabled = false; }
}

function renderMissedDoses(data) {
  const section = document.getElementById("missed-dose-items");
  const adherence = data?.adherence;
  // Use server-provided missed_days (spec §3.1 adherence), not recorded − taken
  const missedCount = adherence?.missed_days;
  if (!adherence || !missedCount) { section.hidden = true; return; }
  section.hidden = false;
  const reasons = adherence.missed_reasons || [];
  const doses = missedCount === 1 ? "1 missed dose" : `${missedCount} missed doses`;
  document.getElementById("missed-dose-summary").textContent =
    `${doses} in the last ${adherence.window_days} days. Worth discussing with your doctor or pharmacist.`;
  const list = document.getElementById("missed-dose-list");
  list.replaceChildren();
  for (const reason of reasons) {
    const li = document.createElement("li");
    li.textContent = `What got in the way: ${reason.label.toLowerCase()}${reason.count > 1 ? ` (${reason.count} times)` : ""}`;
    list.append(li);
  }
}

// Topic chips call POST /patients/{id}/medication/ask with {run_id, topic_id}
async function medicationTopic(topicId) {
  for (const chip of document.querySelectorAll(".topic-chip"))
    chip.setAttribute("aria-pressed", String(chip.dataset.topicId === topicId));
  const answerArea = document.getElementById("medication-answer");
  const ctx = window.auraAgentContext?.();
  if (!ctx?.patientId) return;
  try {
    const response = await fetch(`/patients/${encodeURIComponent(ctx.patientId)}/medication/ask`, {
      method:"POST", headers:{"Content-Type":"application/json"},
      body: JSON.stringify({run_id: window.auraUniqueId(), topic_id: topicId})
    });
    if (!response.ok) throw new Error("Request failed");
    const result = await response.json();
    // BLOCKED means the safety gate stopped the answer — hide it
    if (result.status === "BLOCKED") {
      answerArea.hidden = true;
      return;
    }
    answerArea.hidden = false;
    window.auraMedicationAnswerFor = window.auraAgentContext?.()?.patientId;
    document.getElementById("answer-text").textContent = result.answer || "";
    document.getElementById("answer-source").textContent = result.source_label || "";
  } catch {
    // On error, hide the answer — never show built-in medication text
    answerArea.hidden = true;
  }
}

// Free-text ask (inside the <details> fold)
async function medicationAsk(question) {
  const ctx = window.auraAgentContext?.();
  if (!ctx?.patientId) return;
  const answerArea = document.getElementById("medication-answer");
  try {
    const response = await fetch(`/patients/${encodeURIComponent(ctx.patientId)}/medication/ask`, {
      method:"POST", headers:{"Content-Type":"application/json"},
      body: JSON.stringify({run_id: window.auraUniqueId(), question})
    });
    if (!response.ok) throw new Error("Request failed");
    const result = await response.json();
    // A typed question is saved and safety-checked like any patient text: reload the
    // record so a changed safety state (panel, hidden cards) shows at once.
    if (typeof refresh === "function") { try { await refresh(); } catch { /* existing offline handling */ } }
    if (result.status === "BLOCKED") { answerArea.hidden = true; return; }
    document.getElementById("medication-question").value = "";
    answerArea.hidden = false;
    window.auraMedicationAnswerFor = window.auraAgentContext?.()?.patientId;
    document.getElementById("answer-text").textContent = result.answer || "";
    document.getElementById("answer-source").textContent = result.source_label || "";
  } catch {
    answerArea.hidden = true;
  }
}

async function loadCompanion(patientId) {
  const root = document.getElementById("companion-cards");
  try {
    const response = await fetch(`/patients/${encodeURIComponent(patientId)}/companion`, {cache:"no-store"});
    if (!response.ok) throw new Error("Companion unavailable");
    const data = await response.json();
    window.auraCompanionData = data;
    renderCompanion(data);
  } catch {
    // On any error, hide the cards — never show built-in medication text
    root.hidden = true;
  }
}

// Dose recording — uses the app's existing submit path (window.auraSubmitEvent)
// scheduled_time = current.view.latest_occurred_at, matching the existing
// medication buttons in app.js. "Recorded" shown only after server confirms
// (aura-input-committed event fires only on success). "Not yet" sends nothing.
// Each reason choice sends exactly one MISSED event (with reason when chosen).
function recordDose(status, reason) {
  if (status === "UNKNOWN") return; // "Not yet" sends nothing
  const submit = window.auraSubmitEvent;
  if (!submit) return;
  const payload = {scheduled_time: doseScheduledTime(), status};
  if (status === "MISSED" && reason && reason !== "PREFER_NOT_TO_SAY") payload.reason = reason;
  document.getElementById("dose-saved").textContent = "Recording…";
  let committed = false;
  // One-shot listener: aura-input-committed fires only when the server confirms.
  const handler = () => {
    committed = true;
    const label = status === "ACKNOWLEDGED" ? "Taken" : "Skipped";
    document.getElementById("dose-saved").textContent = `Recorded: ${label}`;
  };
  window.addEventListener("aura-input-committed", handler, {once: true});
  // submitEvent may return early (busy/pending) without committing — clean up
  submit("MEDICATION_EVENT", payload).finally(() => {
    window.removeEventListener("aura-input-committed", handler);
    // If not committed, clear the "Recording…" text
    if (!committed) document.getElementById("dose-saved").textContent = "";
  });
}

function doseScheduledTime() {
  const ctx = window.auraAgentContext?.();
  // Match the existing medication buttons: use latest_occurred_at for fixture patients
  return ctx?.latestOccurredAt || new Date().toISOString();
}

document.addEventListener("click", (event) => {
  const doseBtn = event.target.closest("[data-dose]");
  if (doseBtn) {
    const status = doseBtn.dataset.dose;
    // Update button visual state immediately
    for (const btn of document.querySelectorAll(".dose-btn"))
      btn.setAttribute("aria-pressed", String(btn === doseBtn));
    // Show reason chips if MISSED; hide otherwise
    document.getElementById("dose-reason").hidden = status !== "MISSED";
    // Reset reason chip selection
    for (const chip of document.querySelectorAll(".reason-chip"))
      chip.setAttribute("aria-pressed", "false");
    if (status === "UNKNOWN") {
      document.getElementById("dose-saved").textContent = "";
      return; // "Not yet" sends nothing
    }
    if (status === "ACKNOWLEDGED") {
      recordDose(status);
    }
    // MISSED: wait for a reason chip click before sending
    return;
  }

  const reasonBtn = event.target.closest("[data-reason]");
  if (reasonBtn) {
    const reason = reasonBtn.dataset.reason;
    for (const chip of document.querySelectorAll(".reason-chip"))
      chip.setAttribute("aria-pressed", String(chip === reasonBtn));
    // Each choice sends exactly one MISSED event (with reason when chosen)
    recordDose("MISSED", reason);
    return;
  }

  const askBtn = event.target.closest("#medication-ask-btn");
  if (askBtn) {
    const question = document.getElementById("medication-question").value.trim();
    if (!question) return;
    askBtn.disabled = true;
    medicationAsk(question).finally(() => { askBtn.disabled = false; });
    return;
  }
});

// Hook into the existing render cycle — no polling interval
window.addEventListener("aura-record-view", () => {
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


// Patient side: what the person mentioned (their own words). Hidden when empty or unavailable.
async function loadActivities() {
  const card = document.getElementById("activities-card");
  const patient = window.auraAgentContext?.()?.patientId;
  if (!patient) { card.hidden = true; return; }
  try {
    const response = await fetch(`/patients/${encodeURIComponent(patient)}/activities`, {cache:"no-store"});
    if (!response.ok) throw new Error("unavailable");
    const data = await response.json();
    if (window.auraAgentContext?.()?.patientId !== patient) return;
    const list = document.getElementById("activity-list");
    list.replaceChildren();
    for (const item of (data.items || []).slice(0, 8)) {
      const li = document.createElement("li");
      const what = document.createElement("span"); what.className = "activity-phrase"; what.textContent = `“${item.phrase}”`;
      const meta = document.createElement("span"); meta.className = "activity-meta";
      meta.textContent = [companionDateLabel(item.at), ...item.labels, item.minutes ? (item.minutes % 60 === 0 || item.minutes >= 60 ? `${item.minutes / 60} h` : `${item.minutes} min`) : null].filter(Boolean).join(" · ");
      li.append(what, meta); list.append(li);
    }
    card.hidden = !data.available || !(data.items || []).length;
  } catch { card.hidden = true; }
}
window.auraLoadActivities = loadActivities;

// Called after a note is sent: tag activities, then refresh the patient card.
window.auraExtractActivities = async function () {
  const patient = window.auraAgentContext?.()?.patientId;
  if (!patient) return;
  try { await fetch(`/patients/${encodeURIComponent(patient)}/activities/extract`, {method:"POST"}); } catch { return; }
  await loadActivities();
};

// Clinician side: totals only, no phrases.
window.auraLoadActivitySummary = async function () {
  const card = document.getElementById("activity-summary");
  const patient = window.auraAgentContext?.()?.patientId;
  if (!card || !patient) return;
  try {
    const response = await fetch(`/patients/${encodeURIComponent(patient)}/activities/summary`, {cache:"no-store"});
    if (!response.ok) throw new Error("unavailable");
    const data = await response.json();
    if (window.auraAgentContext?.()?.patientId !== patient) return;
    const rows = document.getElementById("activity-summary-rows");
    rows.replaceChildren();
    const cell = (text) => { const td = document.createElement("td"); td.textContent = text; return td; };
    const span = (row) => `${row.days === 1 ? "1 day" : row.days + " days"}${row.minutes ? ` · ${row.minutes % 60 === 0 || row.minutes >= 60 ? row.minutes / 60 + " h" : row.minutes + " min"} stated` : ""}`;
    for (const row of data.categories || []) {
      const tr = document.createElement("tr");
      tr.append(cell(row.label), cell(span(row.recent)), cell(span(row.earlier)));
      rows.append(tr);
    }
    document.getElementById("activity-summary-window").textContent =
      `${companionDateLabel(data.recent.start)}–${companionDateLabel(data.recent.end)} vs ${companionDateLabel(data.earlier.start)}–${companionDateLabel(data.earlier.end)} · days on which an activity was mentioned`;
    let list = document.getElementById("activity-summary-details");
    if (!list) { list = document.createElement("ul"); list.id = "activity-summary-details"; list.className = "activity-list"; document.getElementById("activity-summary-rows").closest("table").after(list); }
    list.replaceChildren(...(data.details || []).slice(0, 6).map(item => { const li = document.createElement("li"); li.textContent = `“${item.phrase}” · ${companionDateLabel(item.at)}`; return li; }));
    list.hidden = !(data.details || []).length;
    card.hidden = !(data.categories || []).length;
  } catch { card.hidden = true; }
};


// Sharing with the clinician (patient consent). The server filters clinician data; the page
// mirrors it: switches on the patient side, a status line and hidden charts on the clinician side.
const SHARE_NAMES = {notes: "notes", readings: "detailed readings", checkin_history: "daily check-ins", activity_details: "activity details"};
window.auraLoadSharing = async function () {
  const patient = window.auraAgentContext?.()?.patientId;
  if (!patient) return;
  let data;
  try {
    const response = await fetch(`/patients/${encodeURIComponent(patient)}/sharing`, {cache:"no-store"});
    if (!response.ok) return;
    data = await response.json();
  } catch { return; }
  if (window.auraAgentContext?.()?.patientId !== patient) return;
  window.auraSharing = data;
  const shared = Object.fromEntries(data.optional.map(row => [row.id, row.shared]));
  for (const [id, value] of Object.entries(shared)) document.body.dataset["share" + id.replace(/(^|_)(\w)/g, (_, __, c) => c.toUpperCase())] = value ? "yes" : "no";
  const minimum = document.getElementById("sharing-minimum");
  minimum.replaceChildren(...data.minimum.map(text => { const li = document.createElement("li"); li.textContent = text; return li; }));
  const options = document.getElementById("sharing-options");
  options.replaceChildren();
  for (const row of data.optional) {
    const label = document.createElement("label"); label.className = "sharing-option";
    const box = document.createElement("input"); box.type = "checkbox"; box.checked = row.shared; box.dataset.share = row.id;
    box.addEventListener("change", () => saveSharing({[row.id]: box.checked}));
    label.append(box, document.createTextNode(" " + row.label)); options.append(label);
  }
  document.getElementById("sharing-source").textContent = data.source === "demo_default_all"
    ? "Demo: everything is shared until you change it. Changes are recorded with the date."
    : `Your choice${data.updated_at ? `, recorded ${companionDateLabel(data.updated_at)}` : ""}. You can change it any time.`;
  const hidden = data.optional.filter(row => !row.shared).map(row => SHARE_NAMES[row.id]);
  const status = document.getElementById("sharing-status");
  status.textContent = hidden.length
    ? `Shared by the patient: the agreed minimum. Not shared: ${hidden.join(", ")}. Ask the patient if it matters.`
    : "The patient shares everything in this record, including notes and detailed readings.";
  status.hidden = false;
};
async function saveSharing(choices) {
  const patient = window.auraAgentContext?.()?.patientId;
  if (!patient) return;
  try {
    await fetch(`/patients/${encodeURIComponent(patient)}/sharing`, {method:"POST", headers:{"Content-Type":"application/json"}, body: JSON.stringify(choices)});
  } finally { await window.auraLoadSharing(); window.auraLoadActivitySummary?.(); }
}
window.auraSaveSharing = saveSharing;
for (const [id, value] of [["share-all", true], ["share-minimum", false]]) {
  document.getElementById(id)?.addEventListener("click", () => saveSharing({notes:value, readings:value, checkin_history:value, activity_details:value}));
}
