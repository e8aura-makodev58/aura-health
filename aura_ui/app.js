/* Presentation only: all observations, decisions and safety permissions come from APIs. */
"use strict";
const $ = (id) => document.getElementById(id);
const labels = {SLEEP_MIDPOINT: "Sleep time", SLEEP_DURATION: "Sleep duration", ACTIVITY: "Activity", RESTING_HEART_RATE: "Resting heart rate"};
const trustLabels = {PROVISIONAL: "Usual still being learned", TRUSTED: "Usual established", REESTABLISHING: "Usual being learned again"};
const sensingLabels = {OBSERVED: "Data available", UNOBSERVED: "Data unavailable"};
const recordLabels = {PATIENT_CHECKIN: "Check-in", MEDICATION_EVENT: "Medication routine", CONTEXT_EVENT: "Context added", CONTEXT_EXPLANATION: "Explanation added", HELD_FOR_REVIEW: "Held for review", SENSING_GAP: "Wearable data unavailable", SENSING_RETURN: "Wearable data returned", SAFETY_BOUNDARY: "Safety boundary", CLINICIAN_REVIEW_ITEM: "Review item prepared", INPUT_HELD_FOR_SAFETY: "Input held for safety evaluation", ANCHOR_COMMAND: "Governed reference event", PATIENT_FREE_TEXT: "Patient note", REVIEW_COMMAND: "Review preparation"};
// Built-in last-known-good development resource, matching aura_safety/resources.py.
// It remains visible even if every network request fails. No contact is invented.
const offlineBundle = {version: "fixture-unverified-v1", stale: true, notice: "Development fixture: verified Singapore safety contacts pending", resources: [{label: "Development fixture: verified Singapore safety contacts pending", contact_method: null}]};
const offlineText = "AURA cannot assess this input while offline. Hold it for server safety evaluation. The built-in resource panel remains available.";
let patientId = null, catalog = [], current = null, communication = null;
let epoch = 0, busy = false, pending = null, offline = false, dialogKind = "text", lastCheckin = null;
let hosted = false, presentationRole = "patient";
window.auraAgentContext = () => ({patientId, record: current?.evidence,
  revision: current?.view.latest_event_id, offline: offline || Boolean(pending), role: presentationRole});
const selections = new Set();
let plainTerms={patient:[],clinician:[]};
fetch('/assets/plain_terms.json').then(r=>r.json()).then(terms=>{plainTerms=terms;if(current)render();}).catch(()=>{});
// randomUUID requires a secure context; getRandomValues also works on the
// operator-approved synthetic LAN HTTP host. IDs never classify patient input.
window.auraUniqueId = () => {
  if (crypto.randomUUID) return crypto.randomUUID();
  const bytes = crypto.getRandomValues(new Uint8Array(16));
  bytes[6] = (bytes[6] & 15) | 64; bytes[8] = (bytes[8] & 63) | 128;
  const hex = [...bytes].map(value => value.toString(16).padStart(2,"0")).join("");
  return `${hex.slice(0,8)}-${hex.slice(8,12)}-${hex.slice(12,16)}-${hex.slice(16,20)}-${hex.slice(20)}`;
};

// Presentation vocabulary only: original facts remain in the API and explicit technical folds.
window.auraPlain = text => {
  const patient=presentationRole==='patient';
  let copy=String(text??'');
  copy=copy.replace(/\bdegC(?: deviation)?\b/g,'°C');
  copy=copy.replace(/\bUNOBSERVED\b/g,'No watch readings').replace(/\bOBSERVED\b/g,'Readings available').replace(/\bTRUSTED\b/g,patient?'Your usual established':'Baseline established').replace(/\bPROVISIONAL\b/g,'Usual still being learned').replace(/\bREESTABLISHING\b/g,'Usual being learned again');
  if(patient)copy=copy.replace(/Nightly HRV \(RMSSD\)/g,'Time between heartbeats').replace(/minutes since sleep-start midnight/g,'sleep time').replace(/\(\+1d\)/g,'(next day)').replace(/\(\+0d\)/g,'');
  copy=copy.replace(/No configured descriptive drift was found for ([^.]+)\./gi,'No change flagged for $1.').replace(/Insufficient covered data to compare ([^.]+) with its reference\./gi,'Still gathering readings for $1.').replace(/relative to the anchored reference/gi,patient?'than your usual':'than baseline').replace(/relative to the recent rolling pattern/gi,'than your recent pattern');
  const replacements=[[/sleep midpoint/gi,'sleep time'],[/anchored reference|governed personal reference|governed reference/gi,patient?'your usual':'baseline'],[/recent rolling reference|rolling reference|stored rolling mean/gi,'recent average'],[/reference trust/gi,'usual pattern'],[/re-establishing reference|reference being re-established/gi,'usual being learned again'],[/provisional reference/gi,'usual still being learned'],[/personal reference/gi,patient?'your usual':'baseline'],[/rolling versus own reference deviation/gi,'difference from baseline'],[/deviation/gi,'change'],[/consecutive recorded days/gi,'days in a row'],[/recorded days/gi,'days'],[/source extraction/gi,'record summary'],[/transient_change|TRANSIENT_DEVIATION/g,'Recent change'],[/PERSISTENT_DRIFT/g,'Longer change'],[/SENSING_GAP/g,'Watch data unavailable'],[/SENSING_RETURN/g,'Watch data returned'],[/E3_RESEARCH/g,'Newer measure'],[/EXPLAINED_HELD_FOR_REVIEW/g,'Explained, held for review'],[/INPUT_HELD_FOR_SAFETY/g,'Held for safety review']];
  for(const [pattern,replacement] of replacements)copy=copy.replace(pattern,replacement);
  for(const {term,replacement} of plainTerms[patient?'patient':'clinician']||[]){const escaped=term.replace(/[.*+?^${}()|[\]\\]/g,'\\$&');copy=copy.replace(new RegExp(`\\b${escaped}\\b`,'gi'),replacement);}
  if(patient)copy=copy.replace(/\bbaseline\b/gi,'your usual').replace(/\bmedian\b/gi,'middle reading').replace(/\bdrift\b/gi,'change').replace(/\brolling\b/gi,'recent').replace(/\banchored\b/gi,'usual');
  return copy.replace(/\b\d{4}-\d{2}-\d{2}(?:T[\d:.]+(?:Z|[+-]\d\d:\d\d))?\b/g,at=>dateLabel(at));
};
window.auraTechnical = (...children) => {const fold=document.createElement('details');fold.className='technical-details';fold.dataset.technical='';const label=document.createElement('summary');label.textContent='Technical details';fold.append(label,...children);return fold;};
function element(tag, text, className) { const node = document.createElement(tag); if (text !== undefined) node.textContent = window.auraPlain(text); if (className) node.className = className; return node; }
function setText(id, text) { $(id).textContent = id.startsWith('safety-') ? text??'' : window.auraPlain(text); }
function tell(message, error = false) { setText("notice", message); $("notice").classList.toggle("error", error); $("notice").hidden = false; }
function dateLabel(at) {
  if (!at) return "No record yet";
  const options = {day:"numeric", month:"short", year:"numeric", timeZone:/^\d{4}-\d{2}-\d{2}$/.test(at)?'UTC':current?.view.patient.timezone || "UTC"};
  try { return new Intl.DateTimeFormat("en-GB", options).format(new Date(at)); }
  catch { return new Intl.DateTimeFormat("en-GB", {...options,timeZone:"UTC"}).format(new Date(at)); }
}
function signalLabel(key) { return labels[key.signal] || current?.evidence?.signals.find(s=>sameSignal(s.key,key))?.label || 'Wearable reading'; }
function sameSignal(a, b) { return a.signal === b.signal && a.source === b.source && (a.metric || "") === (b.metric || ""); }
// Finite hosted demo action, not context credibility or a clinical classification.
function explanationOptions() { return current.view.explanation_options; }
function number(value) { return value == null ? "Not available" : new Intl.NumberFormat("en-GB", {maximumFractionDigits: 1}).format(value); }
function deviation(value, key) {
  if (value == null) return "Not available";
  const units = {SLEEP_MIDPOINT:"minutes", SLEEP_DURATION:"hours", RESTING_HEART_RATE:"beats/min"};
  return `${number(value)} ${units[key.signal] || key.metric || "recorded units"}`;
}

async function api(path, body) {
  let response;
  try { response = await fetch(path, {method: body === undefined ? "GET" : "POST", headers: {"Content-Type":"application/json"}, body: body === undefined ? undefined : JSON.stringify(body), cache: "no-store"}); }
  catch (cause) { const error = new Error("Connection unavailable"); error.network = true; error.cause = cause; throw error; }
  if (!response.ok) { const result = await response.json().catch(() => ({})); const error = new Error(result.error?.message || "Request could not be completed."); error.status = response.status; throw error; }
  return response.json();
}

function renderResources(bundle) {
  const area = $("safety-resources"); area.replaceChildren();
  const resourceNode=(tag,text,cls)=>{const node=element(tag,undefined,cls);node.textContent=text;return node;};
  area.append(resourceNode("strong", "Separate safety resources"));
  for (const resource of (bundle || offlineBundle).resources) {
    area.append(resourceNode("div", resource.label));
    if (resource.contact_method) area.append(resourceNode("div", resource.contact_method));
  }
  area.append(resourceNode("div", `Resource version: ${(bundle || offlineBundle).version}. ${bundle?.notice || "Unverified development fallback; review pending."}`, "fine"));
  if (!bundle || bundle.stale) area.append(resourceNode("div", "Older or unverified resources are still shown; no verified contact is supplied in this prototype.", "fine"));
}

function showSafety(output) {
  window.dispatchEvent(new Event("aura-record-view"));
  const visible = offline || Boolean(output?.pinned_resources);
  $("safety-panel").hidden = !visible;
  $("retry-connection").hidden = !offline;
  if (!visible) return;
  setText("safety-heading", offline ? "Connection unavailable — input not assessed" : "Safety policy takes priority");
  setText("safety-message", offline ? `${offlineText}${output?.pinned_resources ? " " + output.message : ""}` : output.message);
  renderResources(offline ? offlineBundle : output.pinned_resources);
}

function goPage() {
  const requested = location.hash.slice(1) || "home";
  let page = requested==='disclaimer'?'about':["home", "patterns", "review", "about"].includes(requested) ? requested : "home";
  if (presentationRole === "clinician" && page !== "about") page = "patterns";
  document.body.dataset.role = presentationRole;
  $('baseline-legend').textContent=presentationRole==='patient'?'Your usual':'Baseline';
  $('agent-workspace').hidden=presentationRole==='patient';
  document.body.dataset.page = page;
  $("patient-help").hidden = presentationRole !== "patient" || !current;
  document.querySelector(".bottom-nav").hidden = presentationRole !== "patient" || page === "home" || !current;
  $("clinician-disclosure").hidden = presentationRole !== "clinician";
  $("explain").hidden = presentationRole !== "patient";
  $("patient-role").setAttribute("aria-pressed", String(presentationRole === "patient"));
  $("clinician-role").setAttribute("aria-pressed", String(presentationRole === "clinician"));
  setText("patterns-heading", presentationRole === "clinician" ? "Between appointments" : "Your full data");
  for (const node of document.querySelectorAll(".view")) node.hidden = !current || node.id !== `${page}-view`;
  $("empty-state").hidden = Boolean(current);
  for (const link of document.querySelectorAll("[data-page]")) { if (link.dataset.page === page) link.setAttribute("aria-current", "page"); else link.removeAttribute("aria-current"); }
  // Navigation cannot dismiss or replace the server's safety panel.
  showSafety(communication);
  window.dispatchEvent(new Event("aura-record-view"));
}

async function loadPatient(id) {
  if (pending && id !== patientId) { tell("Reconnect to finish the pending input before changing patients. It is held in memory only.", true); return; }
  const ticket = ++epoch; patientId = id; current = null; communication = null; selections.clear(); lastCheckin = null;
  $("records-panel").open = false; $("recorded-details").open = false;
  goPage(); tell("Loading your recorded context…");
  try {
    const base = `/patients/${encodeURIComponent(id)}`;
    const [view, status, snapshot, timeline, evidence] = await Promise.all([api(`${base}/view`), api(`${base}/status`), api(`${base}/review-snapshot`), api(`${base}/timeline`), api(`${base}/evidence`)]);
    const output = view.latest_event_id ? await api(`${base}/events/${encodeURIComponent(view.latest_event_id)}/communication`, {purpose:"AUTO"}) : null;
    if (ticket !== epoch) return;
    current = {view, status, snapshot, timeline, evidence}; communication = output; offline = false;
    render(); $("notice").hidden = true;
  } catch (error) {
    if (ticket !== epoch) return;
    if (error.network || error.status >= 500) { offline = true; showSafety(communication); }
    tell(error.message, true);
  }
}

async function refresh() {
  const ticket = ++epoch, base = `/patients/${encodeURIComponent(patientId)}`;
  const [view, status, snapshot, timeline, evidence] = await Promise.all([api(`${base}/view`), api(`${base}/status`), api(`${base}/review-snapshot`), api(`${base}/timeline`), api(`${base}/evidence`)]);
  const output = view.latest_event_id ? await api(`${base}/events/${encodeURIComponent(view.latest_event_id)}/communication`, {purpose:"AUTO"}) : null;
  if (ticket !== epoch) return;
  if (JSON.stringify(current?.snapshot) !== JSON.stringify(snapshot)) selections.clear();
  current = {view,status,snapshot,timeline,evidence}; communication = output; offline = false; render();
}

function render() {
  const {view, status} = current;
  setText("patient-label", `${view.patient.display_name} · ${dateLabel(view.latest_occurred_at)}`);
  $("quiet-card").hidden = Boolean(communication?.message && !communication.pinned_resources);
  setText("quiet-heading",communication?.pinned_resources ? "The safety pathway is active." : "No question from AURA right now.");
  setText("home-subtitle", communication?.pinned_resources ? "The policy message and separate resources remain above, on every page." : "You can check in whenever it feels useful.");
  $("talk").disabled = busy;
  setText("communication-message", communication?.message);
  setText("wording-origin",communication?.generation_used?"AI-written":"Fixed wording");
  $("communication-card").hidden = !communication?.message || Boolean(communication.pinned_resources);
  $("clarify").hidden = !["MICRO_CHECKIN", "TARGETED_CLARIFICATION"].includes(status.latest_communication_decision) || !explanationOptions().length;
  setText("routine-name", view.patient.treatment?.medication_name || "Follow your existing clinician-managed routine.");
  setText("routine-schedule", view.patient.treatment?.medication_schedule || "Record only. No dose or schedule recommendation.");
  setText("routine-saved", view.latest_medication ? `Latest record: ${view.latest_medication.status}.` : "Your recorded routine.");
  const latestCheckin = [...current.timeline].reverse().find(record => record.record_type === "PATIENT_CHECKIN");
  setText("checkin-saved", latestCheckin ? `Latest recorded check-in: ${latestCheckin.detail.state}.` : "");
  // Exact server state labels; no missingness/trust calculation happens in the browser.
  const unavailable = status.signals.some(signal => signal.sensing_state === "UNOBSERVED");
  const rebuilding = status.signals.some(signal => signal.trust_state === "REESTABLISHING");
  if (!communication?.pinned_resources && unavailable) setText("home-subtitle", "Wearable data is unavailable. You can still check in.");
  else if (!communication?.pinned_resources && rebuilding) setText("home-subtitle", "Data is back. Your personal reference is being re-established.");
  setText("data-heading", !status.signals.length ? "No wearable observations yet" : unavailable ? "Wearable data unavailable" : rebuilding ? "Data is back. Your usual is being learned again." : "Personal context, at your pace.");
  setText("data-summary", !status.signals.length ? "No wearable records available." : unavailable ? "Wearable data unavailable." : rebuilding ? "Your usual is being learned again." : "Wearable records available.");
  setText("privacy-notice", view.privacy_notice);
  if(hosted) setText("dialog-privacy",`Synthetic examples only; safety gate first. ${view.privacy_notice}`);
  renderPatterns(); renderReview(); window.renderAuraEvidence(current.evidence); goPage();
}

function renderPatterns() {
  const {status, view, timeline} = current;
  const container = $("signal-list"); container.replaceChildren();
  for (const signal of status.signals) {
    const card = element("details", undefined, "card signal-card"), summary=element("summary"), body=element("div",undefined,"details-body");
    summary.append(element("h2", signalLabel(signal)));
    const meta = element("div", undefined, "signal-meta");
    meta.append(element("span", sensingLabels[signal.sensing_state], "badge"), element("span", trustLabels[signal.trust_state], "badge")); summary.append(meta);card.append(summary);
    const drift = status.active_longitudinal_observations.find(item => sameSignal(item.key, signal));
    summary.append(element("span",signal.sensing_state==="UNOBSERVED" ? "No current observation inferred" : drift?.description || "No current descriptive observation", "summary-caption"));
    body.append(element("p", drift?.description || "No current descriptive observation available."));
    if (drift?.attenuated) body.append(element("p", `Relevant context retained: ${drift.benign_contexts.join("; ")}. Other evidence is not cleared.`, "fine"));
    if (signal.sensing_state === "UNOBSERVED") body.append(element("p", "No current value is inferred from the gap.", "fine"));
    if (signal.trust_state === "REESTABLISHING") body.append(element("p", "Your usual is being learned again. Review is still needed.", "fine"));
    const button = element("button", "Reference, coverage & context", "text-button"); button.addEventListener("click", () => showWhy(signal)); body.append(button);card.append(body); container.append(card);
  }
  if (!status.signals.length) container.append(element("p", "No wearable observations yet. You can still check in or raise a concern."));
  setText("patterns-summary","Your measurements and check-ins, with their sources.");
  $("held-list").replaceChildren();
  $("held-section").hidden = !status.held_for_review.length;
  for (const row of status.held_for_review) {
    const held = row.record || row, card = element("section", undefined, "card held-item");
    card.append(element("h3", `${signalLabel(held.key)} · ${held.status === "EXPLAINED_HELD_FOR_REVIEW" ? "Explained, held for review" : "New evidence; open for review"}`), element("p", held.detected_drift.description), element("p", `Your explanation: ${held.explanation}`, "fine"), element("p", "The anchored reference is unchanged. This observation stays available for clinician review.", "fine"), element("p",held.status==="EXPLAINED_HELD_FOR_REVIEW" ? "Repeat prompts for this same change are reduced; the observation is retained." : "New evidence has reopened this item. Your explanation is still retained.","fine"));
    $("held-list").append(card);
  }
  if (!status.held_for_review.length) $("held-list").append(element("p", "No explained observations are currently held."));
  $("context-list").replaceChildren();
  for (const context of view.active_context) $("context-list").append(element("p", `${context.patient_explanation || context.explanation || "Recorded context"} · ${(context.affected_signals || []).map(signal => labels[signal] || signal).join(", ")}`, "fine"));
  if (!view.active_context.length) $("context-list").append(element("p", "No active context recorded."));
  $("explain").disabled = !explanationOptions().length;
  $("timeline-list").replaceChildren();
  const records = timeline.filter(record => recordLabels[record.record_type]).slice(-14).reverse();
  for (const record of records) {
    const li = element("li"); li.append(element("time", dateLabel(record.occurred_at)), element("strong", recordLabels[record.record_type]));
    if (record.detail.state) li.append(element("div", record.detail.state));
    if (record.detail.status) li.append(element("div", record.detail.status === "EXPLAINED_HELD_FOR_REVIEW" ? "Explained, held for review" : record.detail.status));
    $("timeline-list").append(li);
  }
}

function showWhy(selected = null) {
  if (!current) return;
  const area = $("why-content"); area.replaceChildren();
  const drifts = current.status.active_longitudinal_observations.filter(drift => !selected || sameSignal(drift.key, selected));
  area.append(element("p", "Your measurements and check-ins help explain this summary."));
  for (const drift of drifts) {
    const section = element("section", undefined, "why-entry"), baseline = current.status.signals.find(signal => sameSignal(drift.key, signal));
    section.append(element("h3", signalLabel(drift.key)), element("p", drift.description));
    const dl = element("dl");
    const fields = [["Source", drift.key.source], ["Anchored reference", baseline?.anchor ? `Version ${baseline.anchor.version} · ${baseline.anchor.reference_start || ""} — ${baseline.anchor.reference_end || ""}` : "Not created"], ["Current vs recent rolling reference", deviation(drift.current_vs_rolling,drift.key)], ["Rolling vs anchored reference", deviation(drift.rolling_vs_anchor,drift.key)], ["Recorded context", (drift.benign_contexts || []).concat(drift.risk_contexts || []).join("; ") || "None linked"], ["Coverage (0–1)", number(drift.coverage)]];
    for (const [title, value] of fields) dl.append(element("dt", title), element("dd", value));
    const technical=window.auraTechnical(dl);
    if(presentationRole==='clinician')section.append(element('p',`Current reading compared with recent average: ${drift.current_vs_rolling} ${current.evidence.signals.find(s=>sameSignal(s.key,drift.key))?.unit||''}. Recent average compared with baseline: ${drift.rolling_vs_anchor} ${current.evidence.signals.find(s=>sameSignal(s.key,drift.key))?.unit||''}. Data coverage: ${drift.coverage}.`),element('p',baseline?.anchor?`Baseline dates: ${dateLabel(baseline.anchor.reference_start)}–${dateLabel(baseline.anchor.reference_end)}.`:'Baseline still being learned.'));
    section.append(technical); area.append(section);
  }
  if (!drifts.length) {
    area.append(element("p", "No current drift observation is available."));
    for(const baseline of current.status.signals.filter(signal=>!selected || sameSignal(signal,selected))){
      const dl=element("dl"),technical=window.auraTechnical(dl);
      for(const [title,value] of [["Source",baseline.source],["Anchored reference",baseline.anchor?`Version ${baseline.anchor.version} · ${baseline.anchor.reference_start || ""} — ${baseline.anchor.reference_end || ""}`:"Not created"],["Reference trust",trustLabels[baseline.trust_state]],["Coverage (0–1)",number(baseline.rolling.coverage_ratio)]])dl.append(element("dt",title),element("dd",value));
      technical.append(dl);area.append(technical);
    }
  }
  $("why-dialog").showModal();
}

function reviewGroup(title, items) {
  const group = element("details", undefined, "card review-group"),summary=element("summary",title),body=element("div",undefined,"details-body");
  summary.append(element("span",`${items.length} recorded item${items.length===1?"":"s"}`,"summary-caption"));group.append(summary);
  group.open=Boolean(items.length && ["Meaningful observations","Explained & held for review","Questions you recorded"].includes(title));
  if (!items.length) body.append(element("p", "None recorded for this review period."));
  else body.append(element("p","Not sent","fine"));
  items.forEach((text, index) => {
    const key = `${title}:${index}`, label = element("label"), box = element("input"); box.type = "checkbox"; box.checked = selections.has(key);
    box.addEventListener("change", () => { if (box.checked) selections.add(key); else selections.delete(key); selectionSummary(); });
    label.append(box, element("span", text)); body.append(label);
  });group.append(body); $("review-list").append(group);
}
function selectionSummary() { setText("selection-summary", `${selections.size} item${selections.size === 1 ? "" : "s"} selected for this temporary preview. Nothing is sent or saved as approval.`); }
function renderReview() {
  const snapshot = current.snapshot; $("review-list").replaceChildren();
  const ready = snapshot.meaningful_longitudinal_changes.length + snapshot.patient_checkin_trend.slice(-7).length + snapshot.medication_routine_events.length + snapshot.active_context.length + snapshot.explained_held_for_review.length + snapshot.unresolved_items.length + snapshot.safety_episode_references.filter(row=>row.episode_id).length + snapshot.patient_selected_questions.length;
  setText("appointment-ready", `${ready} item${ready===1?"":"s"} ready · Not sent`);
  const preview=$("appointment-preview"); preview.replaceChildren(element("h2","A note to look through"));
  for(const change of snapshot.meaningful_longitudinal_changes.slice(0,3)) preview.append(element("p",`${change.latest.description} Recorded ${dateLabel(change.first_seen)} — ${dateLabel(change.last_seen)}.`));
  if(!snapshot.meaningful_longitudinal_changes.length)preview.append(element("p","No recent changes to include."));
  const last=snapshot.patient_checkin_trend.at(-1);
  if(last)preview.append(element("p",`Latest check-in you recorded: ${last.state}, ${dateLabel(last.at)}.`));
  for(const row of snapshot.explained_held_for_review){const held=row.record||row;preview.append(element("p",`${held.detected_drift.description} Your explanation: ${held.explanation}. The observation and your own reference are retained.`));}
  for(const question of snapshot.patient_selected_questions)preview.append(element("p",`Question you recorded: ${question}`));
  preview.append(element("p","Not sent · sources below","fine"));
  setText("review-period", `${dateLabel(snapshot.review_period.start)} — ${dateLabel(snapshot.review_period.end)}`);
  reviewGroup("Reference & data availability", current.status.signals.map(signal => `${signalLabel(signal)} · ${sensingLabels[signal.sensing_state]} · ${trustLabels[signal.trust_state]} · coverage ${number(signal.rolling.coverage_ratio)}`));
  reviewGroup("Meaningful observations", snapshot.meaningful_longitudinal_changes.map(change => change.latest.description));
  reviewGroup("Your recent check-ins", snapshot.patient_checkin_trend.slice(-7).map(checkin => `${dateLabel(checkin.at)} · ${checkin.state}`));
  reviewGroup("Medication-routine records", snapshot.medication_routine_events.map(event => `${dateLabel(event.at)} · ${event.status}`));
  reviewGroup("Active context", snapshot.active_context.map(context => context.patient_explanation || context.explanation || "Recorded context"));
  reviewGroup("Explained & held for review", snapshot.explained_held_for_review.map(row => { const held = row.record || row; return `${held.detected_drift.description} Explanation: ${held.explanation}. Anchored reference retained.`; }));
  reviewGroup("Unresolved review items", snapshot.unresolved_items.map(item => item.summary));
  // Present only real episode references. The underlying accepted snapshot stays intact.
  reviewGroup("Safety interactions", snapshot.safety_episode_references.filter(reference => reference.episode_id).map(reference => 'Safety interaction recorded'));
  reviewGroup("Questions you recorded", snapshot.patient_selected_questions);
  selectionSummary();
}

function openInput(kind = "text") {
  if (!current || busy) return;
  dialogKind = kind; $("input-text").value = ""; $("explanation-fields").hidden = kind !== "explanation";
  $("input-text").readOnly=false;
  setText("input-text-label",kind==='explanation'?'Your explanation':'Your note');
  $("input-text").setAttribute("aria-label",'Your note');
  $("send-input").disabled=false;
  $("fixture-buttons").hidden = !catalog.length || kind === "explanation";
  for (const button of document.querySelectorAll("[data-fixture]")) button.hidden = button.dataset.purpose !== kind;
  for(const button of document.querySelectorAll("[data-fixture]"))button.setAttribute("aria-pressed","false");
  setText("dialog-heading", kind === "explanation" ? "Keep an explanation with this change." : kind === "question" ? "A question for your next review." : hosted ? "Try a conversation example" : "What would you like to share?");
  setText("dialog-copy", kind === "explanation" ? "Keep context alongside the recorded change." : "Enter a synthetic note. Safety evaluation comes first.");
  setText("send-input", kind === "explanation" ? "Keep explanation for review" : "Submit note");
  if (kind === "explanation") {
    if (!explanationOptions().length) { tell("No supported linked explanation is available. Arbitrary explanations are not automatically judged credible."); return; }
    const select = $("explanation-context"); select.replaceChildren();
    for (const context of explanationOptions()) { const option = element("option", context.explanation || "Linked context"); option.value = context.context_event_id; select.append(option); }
    populateExplanation();
  }
  $("input-dialog").showModal();
}
function populateExplanation() {
  const context = current.view.explanation_options.find(item => item.context_event_id === $("explanation-context").value);
  $("explanation-signals").replaceChildren();
  for (const signal of context.affected_signals) { const label = element("label"), checkbox = element("input"); checkbox.type = "checkbox"; checkbox.value = signal; checkbox.checked = true; label.append(checkbox, element("span", labels[signal] || signal)); $("explanation-signals").append(label); }
  $("input-text").value = context.explanation || "";
}
function eventEnvelope(type, payload) {
  const id = window.auraUniqueId();
  // The fixture date is shown explicitly, not passed as hidden scenario information.
  const at = catalog.some(item => item.patient_id === patientId) ? current.view.latest_occurred_at : new Date().toISOString();
  return {event_id:id, event_type:type, occurred_at:at, source:"patient", payload, correlation_id:id, idempotency_key:id};
}
async function submitEvent(type, payload, special = false) {
  if (busy || !current) return;
  if (pending) { tell("A previous input is pending. Reconnect to retry it first.", true); return; }
  const envelope = eventEnvelope(type, payload), body = special ? {event_id:envelope.event_id, occurred_at:envelope.occurred_at, correlation_id:envelope.correlation_id, idempotency_key:envelope.idempotency_key, ...payload} : envelope;
  pending = {path:`/patients/${encodeURIComponent(patientId)}/${special ? "context-explanations" : "events"}`, body};
  await sendPending();
}
async function sendPending() {
  if (busy || !pending) return; busy = true; toggleBusy(true);
  try {
    await api(pending.path, pending.body);
    pending = null; $("input-dialog").close();
    await refresh(); tell("Recorded. Nothing has been sent to a clinician.");
    window.dispatchEvent(new CustomEvent('aura-input-committed'));
  } catch (error) {
    if (error.network || error.status >= 500) {
      offline = true; showSafety(communication);
      $("input-dialog").close();
      tell(pending ? "Not confirmed by the server. Keep this page open; the input is held in memory only and will retry with the same idempotency key when connected. Reloading loses unsent text." : "Saved input, but current state could not be reloaded. Reconnect to confirm safety state.", true);
    } else { pending = null; tell(error.message, true); }
  } finally { busy = false; toggleBusy(false); }
}
function toggleBusy(value) { for (const node of document.querySelectorAll("[data-checkin],[data-medication],#send-input,#scenario,#connect,#talk")) node.disabled = value; if(!value && hosted && !$("input-text").value) $("send-input").disabled=true; }

$("demo-toggle").addEventListener("click", () => { $("demo-panel").hidden = !$("demo-panel").hidden; $("demo-toggle").setAttribute("aria-expanded", String(!$("demo-panel").hidden)); });
$("start-demo").addEventListener("click", () => { $("demo-panel").hidden = false; $("demo-toggle").setAttribute("aria-expanded", "true"); $("scenario").focus(); });
$("scenario").addEventListener("change", () => { location.hash = "home"; loadPatient($("scenario").value); });
$("connect").addEventListener("click", () => { if ($("patient-id").value.trim()) loadPatient($("patient-id").value.trim()); });
for (const button of document.querySelectorAll("[data-checkin]")) button.addEventListener("click", async () => { lastCheckin = button.dataset.checkin; await submitEvent("PATIENT_CHECKIN", {state:lastCheckin}); });
for (const button of document.querySelectorAll("[data-medication]")) button.addEventListener("click", () => { const at = catalog.some(item => item.patient_id === patientId) ? current?.view.latest_occurred_at : new Date().toISOString(); submitEvent("MEDICATION_EVENT", {scheduled_time:at, status:button.dataset.medication.toUpperCase()}); });
$("talk").addEventListener("click", () => openInput("text")); $("add-note").addEventListener("click", () => openInput("text"));
$("clarify").addEventListener("click", () => openInput("explanation")); $("explain").addEventListener("click", () => openInput("explanation"));
$("add-question").addEventListener("click", () => openInput("question"));
$("why-home").addEventListener("click", () => showWhy());
$("why-patterns").addEventListener("click", () => showWhy());
$("chart-range").addEventListener("change", () => { if(current) window.renderAuraEvidence(current.evidence); });
for (const role of ["patient", "clinician"]) $(`${role}-role`).addEventListener("click", () => {
  presentationRole = role; location.hash = "home"; if(current)render();else goPage(); window.scrollTo(0,0);
});
$("close-dialog").addEventListener("click", () => $("input-dialog").close()); $("close-why").addEventListener("click", () => $("why-dialog").close());
$("explanation-context").addEventListener("change", populateExplanation);
for (const button of document.querySelectorAll("[data-fixture]")) button.addEventListener("click", () => { $("input-text").value = button.dataset.fixture;for(const option of document.querySelectorAll("[data-fixture]"))option.setAttribute("aria-pressed",String(option===button));$("send-input").disabled=busy; });
$("input-form").addEventListener("submit", async (event) => {
  event.preventDefault(); const text = $("input-text").value.trim(); if (!text) return;
  if (dialogKind === "explanation") {
    const context = current.view.explanation_options.find(item => item.context_event_id === $("explanation-context").value);
    const signals = [...document.querySelectorAll("#explanation-signals input:checked")].map(input => input.value);
    if (!signals.length) { tell("Select an associated observation.", true); return; }
    await submitEvent("CONTEXT_EXPLANATION", {context_event_id:context.context_event_id, relevant_drift_ref:null, explanation:text, affected_signals:signals}, true);
  } else if (dialogKind === "question") await submitEvent("REVIEW_COMMAND", {action:"ADD_QUESTION", question:text});
  else await submitEvent("PATIENT_FREE_TEXT", {text});
});
window.addEventListener("hashchange",()=>{goPage();window.scrollTo(0,0);});
$("retry-connection").addEventListener("click", async () => {
  if (busy) return;
  if (pending) await sendPending();
  else if (patientId && current) { try { await refresh(); tell("Server state reloaded."); } catch (error) { offline = true; showSafety(communication); tell(error.message, true); } }
  else await start();
});
$("reset-demo").addEventListener("click", async () => {
  if (busy || pending) { tell("Finish the pending input before resetting the synthetic session.",true); return; }
  if (!window.confirm("Restore this synthetic session to seed 7? This is demo tooling, not a patient safety transition.")) return;
  busy = true; toggleBusy(true);
  try {
    await api("/demo/reset",{confirm:"RESET_SYNTHETIC_SESSION"});
    await loadPatient(catalog[0].patient_id);
    $("scenario").value = catalog[0].patient_id;
    tell("Synthetic session restored. Other visitors were not changed.");
  } catch(error) { tell(error.message,true); }
  finally { busy = false; toggleBusy(false); }
});
window.addEventListener("offline", () => { offline = true; showSafety(communication); tell("Connection unavailable. No input is assessed locally. Resources remain visible.", true); });
window.addEventListener("online", async () => { if (pending) await sendPending(); else if (current) { try { await refresh(); tell("Connection restored; server state reloaded."); } catch { offline = true; showSafety(communication); } } });
window.addEventListener("beforeunload", (event) => { if (pending) { event.preventDefault(); event.returnValue = "Unconfirmed input is held in memory only."; } });
document.addEventListener("aura-settings-updated",async()=>{if(current){try{await refresh();}catch{tell("Provider settings changed; reload context when connected.",true);}}});

async function start() {
  goPage();
  try {
    const result = await api("/demo/scenarios"); catalog = result.scenarios; hosted = Boolean(result.hosted);
    presentationRole = "clinician"; $("role-switch").hidden = false;
    $("hosted-notice").hidden = true; $("reset-demo").hidden = !result.can_reset;
    $("connect-form").hidden = hosted;
    if (hosted) setText("dialog-privacy","Synthetic input only. Unavailable safety evaluation holds the note.");
    $("scenario").replaceChildren();
    $("scenario").disabled = false;
    for (const scenario of catalog) { const option = element("option", scenario.label); option.value = scenario.patient_id; $("scenario").append(option); }
    const initial = catalog.find(item => item.id === "B") || catalog[0];
    $("scenario").value = initial.patient_id;
    await loadPatient(initial.patient_id);
  } catch (error) {
    $("scenario").replaceChildren(element("option", "Demo temporarily unavailable")); $("scenario").disabled = true;
    tell(error.message, true);
    if (error.network || error.status >= 500 || error.status === 409) { offline = true; showSafety(null); }
  }
}
start();
