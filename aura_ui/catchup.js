/* Past medication records, calendar, welcome back and record coverage (spec §9.3, IDs §9.5).
   Presentation only. Nothing is saved until the patient presses Save; the server checks every day.
   Safety state always takes priority: the prompt only appears in the normal state. */
"use strict";

(() => {
const byId = id => document.getElementById(id);
const STATUS = {ACKNOWLEDGED: {mark: "✓", label: "Taken"}, MISSED: {mark: "✕", label: "Missed"}, UNKNOWN: {mark: "?", label: "Not sure"}};
const CYCLE = [null, "ACKNOWLEDGED", "MISSED", "UNKNOWN"];
const CHECKIN = {Good: "Good", Okay: "Okay", Rough: "Rough"};
const patient = () => window.auraAgentContext?.()?.patientId || null;
const role = () => document.body.dataset.role || "patient";
const base = () => `/patients/${encodeURIComponent(patient())}`;
const longDate = iso => new Intl.DateTimeFormat("en-GB", {weekday: "short", day: "numeric", month: "short", timeZone: "UTC"}).format(new Date(iso + "T00:00:00Z"));
const monthName = ym => new Intl.DateTimeFormat("en-GB", {month: "long", year: "numeric", timeZone: "UTC"}).format(new Date(ym + "-01T00:00:00Z"));
const el = (tag, text, cls) => { const node = document.createElement(tag); if (text != null) node.textContent = text; if (cls) node.className = cls; return node; };
async function getJSON(path, body) {
  const response = await fetch(path, body === undefined ? {cache: "no-store"} :
    {method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify(body)});
  const data = await response.json().catch(() => ({}));
  if (!response.ok) { const error = new Error(data.error?.message || "That didn't work. Please try again."); error.code = data.error?.code; throw error; }
  return data;
}

/* ---- dose card line: gentle prompt for unrecorded past days ---------------------------- */
function dismissedKey() { return `aura-med-update-dismissed:${patient()}`; }
function renderGap(data) {
  const line = byId("med-update-line");
  const gap = data?.safety_normal ? data.medication_gap : null;
  let dismissed = false;
  try { dismissed = sessionStorage.getItem(dismissedKey()) === "1"; } catch { /* storage unavailable */ }
  line.hidden = !gap?.prompt || dismissed;
  if (gap?.prompt) byId("med-update-text-line").textContent =
    `${gap.unresolved_days} of the last ${gap.window_days} days have no medication record. You can fill them in if you'd like.`;
}
if (typeof renderCompanion === "function") {
  const baseRender = renderCompanion;
  // eslint-disable-next-line no-global-assign
  renderCompanion = function (data) { baseRender(data); renderGap(data); renderWelcomeBack(); updateShortcuts(); };
}
byId("med-update-dismiss").addEventListener("click", () => {
  try { sessionStorage.setItem(dismissedKey(), "1"); } catch { /* storage unavailable */ }
  byId("med-update-line").hidden = true;
});

/* ---- update dialog -------------------------------------------------------------------- */
const state = {window: null, days: new Map(), requestId: null, question: false};
function resetDialog() {
  state.days = new Map(); state.question = false; state.requestId = window.auraUniqueId();
  byId("med-update-text").value = ""; byId("med-update-message").textContent = "";
  byId("med-update-preview").hidden = true; byId("med-update-key").hidden = true;
  byId("med-update-question").hidden = true; byId("med-update-result").hidden = true;
  byId("med-update-save").hidden = false;
  for (const id of ["med-update-text", "med-update-interpret", "med-update-tap"]) byId(id).disabled = false;
}
async function openUpdate(focusDate) {
  resetDialog();
  const dialog = byId("med-update-dialog");
  state.window = null;
  try { state.window = await getJSON(`${base()}/medication/update-window`); }
  catch (error) {
    // Nothing to edit without the server's window: say so and leave only Close.
    for (const id of ["med-update-text", "med-update-interpret", "med-update-tap"]) byId(id).disabled = true;
    byId("med-update-message").textContent = `${error.message} Please close this and try again.`;
    byId("med-update-save").disabled = true; dialog.showModal(); return;
  }
  dialog.showModal();
  if (focusDate) { byId("med-update-message").textContent = "Tap a day to set it."; showPreview(focusDate); }
  updateSave();
}
function showPreview(focusDate) {
  if (!state.window) return;
  const preview = byId("med-update-preview");
  preview.replaceChildren();
  for (const day of state.window.days) {
    const chosen = state.days.get(day.date);
    const status = day.locked ? day.status : chosen?.status || null;
    const button = el("button", null, "med-day");
    button.type = "button";
    Object.assign(button.dataset, {date: day.date, status: status || "", basis: day.locked ? "recorded" : chosen?.basis || "", locked: String(day.locked)});
    button.disabled = day.locked;
    button.append(el("span", day.weekday, "med-day-week"), el("span", String(Number(day.date.slice(8))), "med-day-num"),
                  el("span", status ? STATUS[status].mark : "·", "med-day-mark"));
    const words = status ? STATUS[status].label : "No record";
    button.setAttribute("aria-label", `${longDate(day.date)}: ${words}${day.locked ? ", already recorded" : chosen?.basis === "from_most_days" ? ", from \"most days\"" : ""}`);
    if (!day.locked) button.addEventListener("click", () => {
      const next = CYCLE[(CYCLE.indexOf(state.days.get(day.date)?.status || null) + 1) % CYCLE.length];
      if (next) state.days.set(day.date, {status: next, basis: "explicit"}); else state.days.delete(day.date);
      showPreview(day.date); updateSave();
      byId("med-update-message").textContent = `${longDate(day.date)}: ${next ? STATUS[next].label : "no record"}.`;
    });
    preview.append(button);
  }
  preview.hidden = false; byId("med-update-key").hidden = false;
  if (focusDate) preview.querySelector(`.med-day[data-date="${focusDate}"]`)?.focus();
}
function updateSave() {
  const count = [...state.days.values()].filter(day => day.status).length;
  const save = byId("med-update-save");
  save.disabled = !count || state.question;
  save.textContent = count ? `Save ${count} ${count === 1 ? "day" : "days"}` : "Save these days";
}
byId("med-update-open").addEventListener("click", () => openUpdate());
byId("med-update-close").addEventListener("click", () => byId("med-update-dialog").close());
byId("med-update-tap").addEventListener("click", () => { byId("med-update-message").textContent = "Tap a day to set it."; showPreview(); updateSave(); });
byId("med-update-interpret").addEventListener("click", async () => {
  const text = byId("med-update-text").value.trim();
  const message = byId("med-update-message");
  if (!text) { message.textContent = "Write a few words first, or tap the days instead."; return; }
  const button = byId("med-update-interpret");
  button.disabled = true; message.textContent = "AURA is reading that…";
  let result;
  try { result = await getJSON(`${base()}/medication/update/interpret`, {request_id: window.auraUniqueId(), text}); }
  catch (error) { message.textContent = error.message; button.disabled = false; return; }
  button.disabled = false;
  if (result.status === "BLOCKED") {
    // The safety pathway takes over; the dialog steps aside.
    byId("med-update-dialog").close();
    await window.auraRefresh?.();
    return;
  }
  state.window = result.window || state.window;
  for (const day of result.days || []) state.days.set(day.date, {status: day.status, basis: day.basis});
  const notes = [];
  if (result.message) notes.push(result.message);
  if (result.status === "PROPOSED") notes.push("Check the days below. Tap any day to change it.");
  if (result.out_of_window?.length) notes.push("Some days you mentioned are more than two weeks ago, so they can't be updated here.");
  message.textContent = notes.join(" ");
  const question = result.status === "PROPOSED" ? result.question : null;
  state.question = Boolean(question);
  byId("med-update-question").hidden = !question;
  if (question) byId("med-update-question-text").textContent = question;
  showPreview(); updateSave();
});
byId("med-update-yes").addEventListener("click", () => {
  for (const [date, day] of state.days) if (day.basis === "from_most_days") state.days.set(date, {...day, basis: "explicit"});
  state.question = false; byId("med-update-question").hidden = true;
  byId("med-update-message").textContent = "Thanks. Check the days, then save.";
  showPreview(); updateSave();
});
byId("med-update-no").addEventListener("click", () => {
  for (const [date, day] of state.days) if (day.basis === "from_most_days") state.days.delete(date);
  state.question = false; byId("med-update-question").hidden = true;
  byId("med-update-message").textContent = "Okay. Those other days are left blank. Tap any you remember.";
  showPreview(); updateSave();
});
byId("med-update-save").addEventListener("click", async () => {
  const days = [...state.days.entries()].filter(([, day]) => day.status).map(([date, day]) => ({date, status: day.status}));
  const result = byId("med-update-result");
  byId("med-update-save").disabled = true;
  try {
    const saved = await getJSON(`${base()}/medication/update`, {request_id: state.requestId, days});
    state.window = saved.window; state.days = new Map();
    result.textContent = saved.status === "HELD"
      ? "AURA couldn't finish its safety check, so these days are waiting and aren't saved yet. Nothing more to do right now."
      : `Saved ${saved.saved.length} ${saved.saved.length === 1 ? "day" : "days"}. They're marked as filled in later.`;
    result.hidden = false; byId("med-update-save").hidden = true; byId("med-update-key").hidden = true;
    byId("med-update-question").hidden = true;
    showPreview();
    for (const id of ["med-update-text", "med-update-interpret", "med-update-tap"]) byId(id).disabled = true;
    if (saved.status === "HELD") await window.auraRefresh?.();
    else if (typeof loadCompanion === "function") loadCompanion(patient());
    if (!byId("calendar-view").hidden) loadCalendar(calendarMonth);
  } catch (error) {
    result.textContent = error.code === "UPDATE_CONFLICT" ? "One of those days already has a record. Please open this again to see the latest."
      : error.code === "SAFETY_ACTIVE" ? error.message : `${error.message} It's safe to press Save again.`;
    result.hidden = false; updateSave();
  }
});

/* ---- calendar ------------------------------------------------------------------------- */
let calendarMonth = null, calendarData = null, calendarFor = null;
function shiftMonth(ym, by) { const d = new Date(ym + "-01T00:00:00Z"); d.setUTCMonth(d.getUTCMonth() + by); return d.toISOString().slice(0, 7); }
function renderLegend() {
  const legend = byId("calendar-legend");
  legend.replaceChildren(el("h2", "What the marks mean"));
  const list = el("ul");
  const rows = [["cal-med", "ACKNOWLEDGED", "✓", "Medication taken"], ["cal-med", "MISSED", "✕", "Medication missed"],
                ["cal-med", "UNKNOWN", "?", "Not sure"], ["cal-med later", "ACKNOWLEDGED", "✓", "Filled in later (ring)"]];
  for (const [cls, status, mark, words] of rows) {
    const item = el("li"); const sample = el("span", mark, cls); sample.dataset.status = status;
    if (cls.includes("later")) sample.dataset.reportedLater = "true";
    item.append(sample, el("span", words)); list.append(item);
  }
  if (!calendarData?.withheld.includes("checkin_history"))
    for (const state of ["Good", "Okay", "Rough"]) { const item = el("li"); const dot = el("span", null, "cal-checkin"); dot.dataset.state = state; item.append(dot, el("span", `Check-in: ${state}`)); list.append(item); }
  if (!calendarData?.withheld.includes("readings")) { const item = el("li", null, "cal-cover-legend"); item.append(el("span", null, "cal-cover sample"), el("span", "Watch data recorded")); list.append(item); }
  legend.append(list, el("p", "A blank day means nothing was recorded, not that all was well.", "fine"));
}
async function loadCalendar(month) {
  const grid = byId("calendar-grid");
  const viewer = role() === "clinician" ? "clinician" : "patient";
  try { calendarData = await getJSON(`${base()}/calendar?viewer=${viewer}${month ? `&month=${month}` : ""}`); }
  catch (error) { grid.replaceChildren(el("p", error.message, "fine")); return; }
  calendarMonth = calendarData.month; calendarFor = `${patient()}:${viewer}`;
  byId("calendar-month").textContent = monthName(calendarMonth);
  byId("calendar-prev").disabled = calendarMonth <= calendarData.record_start.slice(0, 7);
  byId("calendar-next").disabled = calendarMonth >= calendarData.today.slice(0, 7);
  grid.replaceChildren();
  const lead = (new Date(calendarMonth + "-01T00:00:00Z").getUTCDay() + 6) % 7;
  for (let i = 0; i < lead; i++) grid.append(el("span", null, "cal-blank"));
  for (const day of calendarData.days) {
    const cell = el("button", null, "cal-day");
    cell.type = "button"; cell.dataset.date = day.date;
    const before = day.date < calendarData.record_start;
    cell.disabled = day.future || before;
    if (day.date === calendarData.today) cell.classList.add("today");
    cell.append(el("span", String(Number(day.date.slice(8))), "cal-num"));
    const marks = el("span", null, "cal-marks");
    if (day.medication) {
      const med = el("span", STATUS[day.medication.status].mark, "cal-med");
      med.dataset.status = day.medication.status; med.dataset.reportedLater = String(day.medication.reported_later);
      marks.append(med);
    }
    if (day.checkin) { const dot = el("span", null, "cal-checkin"); dot.dataset.state = day.checkin; marks.append(dot); }
    if (day.note || day.activity) marks.append(el("span", "✎", "cal-note"));
    cell.append(marks);
    if (day.coverage) { const bar = el("span", null, "cal-cover"); bar.dataset.coverage = day.coverage; cell.append(bar); }
    const words = [longDate(day.date), day.medication ? `medication ${STATUS[day.medication.status].label.toLowerCase()}${day.medication.reported_later ? ", filled in later" : ""}` : "no medication record",
                   day.checkin ? `check-in ${day.checkin}` : null].filter(Boolean).join(", ");
    cell.setAttribute("aria-label", words);
    cell.addEventListener("click", () => loadDay(day.date));
    grid.append(cell);
  }
  renderLegend();
  byId("calendar-detail").hidden = true;
}
function formatReading(row, clinician) {
  if (row.signal === "SLEEP_MIDPOINT") {
    const minutes = ((Math.round(row.value) % 1440) + 1440) % 1440;
    const clock = `${String(Math.floor(minutes / 60)).padStart(2, "0")}:${String(minutes % 60).padStart(2, "0")}`;
    return clinician ? `${row.label}: midpoint ${clock} (${Math.round(row.value)} ${row.unit})` : `Middle of your sleep: about ${clock}`;
  }
  if (row.signal === "SLEEP_DURATION") return `${row.label}: ${row.value.toFixed(1)} hours`;
  if (row.signal === "ACTIVITY") return `${clinician ? row.label : "Steps"}: ${Math.round(row.value).toLocaleString("en-GB")}${clinician ? ` ${row.unit}` : ""}`;
  if (row.signal === "RESTING_HEART_RATE") return `${row.label}: ${Math.round(row.value)} beats a minute`;
  return `${row.label}: ${Math.round(row.value * 10) / 10}${clinician ? ` ${row.unit}` : ""}`;
}
async function loadDay(date) {
  const detail = byId("calendar-detail");
  const clinician = role() === "clinician";
  let day;
  try { day = await getJSON(`${base()}/calendar/${date}?viewer=${clinician ? "clinician" : "patient"}`); }
  catch (error) { detail.replaceChildren(el("p", error.message)); detail.hidden = false; return; }
  for (const cell of document.querySelectorAll("#calendar-grid .cal-day")) cell.setAttribute("aria-pressed", String(cell.dataset.date === date));
  const notShared = what => el("p", `Not shared by the patient: ${what}. Ask the patient if it matters.`, "fine not-shared");
  detail.replaceChildren(el("h2", longDate(date)));
  const section = (title, ...children) => { const block = el("div", null, "cal-section"); block.append(el("h3", title), ...children); detail.append(block); };
  const med = day.medication;
  const medLine = med ? `${STATUS[med.status].label}${med.reason ? ` · ${med.reason}` : ""}${med.reported_later ? ` · filled in later, on ${longDate(med.reported_on)}` : ""}` : "No record for this day.";
  const medBlock = [el("p", medLine)];
  if (!clinician && !med) {
    const inWindow = (date >= shiftDays(day.today, -13)) && date <= day.today;
    if (inWindow) { const button = el("button", "Update this day's medication", "text-button"); button.type = "button"; button.id = "calendar-update-day"; button.addEventListener("click", () => openUpdate(date)); medBlock.push(button); }
  }
  section("Medication", ...medBlock);
  if (day.withheld.includes("checkin_history")) section("Check-in", notShared("each day's check-in"));
  else section("Check-in", el("p", day.checkin ? (clinician ? `Patient check-in: ${day.checkin}` : `You said: ${day.checkin}`) : "No check-in this day."));
  if (day.readings === null) section("Watch readings", notShared("detailed readings"));
  else section("Watch readings", ...(day.readings.length ? [list(day.readings.map(row => formatReading(row, clinician)))] : [el("p", "No watch readings this day.")]));
  if (day.gaps.length) section("Gaps", el("p", `No watch data for: ${day.gaps.join(", ").toLowerCase()}.`));
  if (day.notes === null) section(clinician ? "Notes" : "Your notes", notShared("notes"));
  else if (day.notes.length) section(clinician ? "Patient notes" : "Your notes", list(day.notes));
  if (day.activities === null) section("Activities", notShared("what they mentioned doing"));
  else if (day.activities.length) section(clinician ? "Mentioned activities" : "Things you mentioned", list(day.activities.map(item => `${item.phrase}${item.minutes ? ` (${item.minutes >= 60 ? `${Math.round(item.minutes / 6) / 10} h` : `${item.minutes} min`})` : ""}`)));
  if (day.ideas_chosen?.length) section(clinician ? "Ideas chosen" : "Ideas you picked", list(day.ideas_chosen));
  if (day.findings.length) section(clinician ? "Changes in this period" : "Changes AURA noticed",
    list(day.findings.map(row => clinician ? `${row.label}: ${row.direction.replaceAll("_", " ").toLowerCase()} (first detected ${longDate(row.since)})` : `A change in your ${row.label.toLowerCase()}, first noticed ${longDate(row.since)}`)));
  detail.hidden = false;
  const still = window.matchMedia?.("(prefers-reduced-motion: reduce)").matches;
  detail.scrollIntoView({block: "nearest", behavior: still ? "auto" : "smooth"});
}
function list(items) { const ul = el("ul"); for (const text of items) ul.append(el("li", text)); return ul; }
function shiftDays(iso, by) { const d = new Date(iso + "T00:00:00Z"); d.setUTCDate(d.getUTCDate() + by); return d.toISOString().slice(0, 10); }
byId("calendar-prev").addEventListener("click", () => loadCalendar(shiftMonth(calendarMonth, -1)));
byId("calendar-next").addEventListener("click", () => loadCalendar(shiftMonth(calendarMonth, 1)));
byId("clinician-calendar-link").addEventListener("click", () => { location.hash = "calendar"; });
window.addEventListener("aura-record-view", () => {
  const onCalendar = document.body.dataset.page === "calendar" && patient();
  byId("calendar-back").hidden = role() !== "clinician";
  // Load on arrival (fresh data each visit) or when the patient or viewer changes.
  if (onCalendar && calendarFor !== `${patient()}:${role() === "clinician" ? "clinician" : "patient"}`) {
    calendarFor = `${patient()}:${role() === "clinician" ? "clinician" : "patient"}`; loadCalendar(null);
  }
  if (!onCalendar) calendarFor = null;
  if (role() === "clinician") loadCoverage();
});

/* ---- home shortcuts: jump to a card, or open a page ------------------------------------ */
function updateShortcuts() {
  // A shortcut shows only when its card does (the safety pathway hides the companion cards).
  for (const link of document.querySelectorAll("#home-shortcuts [data-jump]")) {
    const card = byId(link.dataset.jump);
    link.hidden = !card || card.hidden || card.closest("[hidden]") !== null;
  }
}
for (const link of document.querySelectorAll("#home-shortcuts [data-jump]")) link.addEventListener("click", event => {
  event.preventDefault();
  const card = byId(link.dataset.jump);
  if (!card) return;
  const still = window.matchMedia?.("(prefers-reduced-motion: reduce)").matches;
  card.setAttribute("tabindex", "-1");
  card.scrollIntoView({block: "start", behavior: still ? "auto" : "smooth"});
  card.focus({preventScroll: true});
});
window.addEventListener("aura-record-view", updateShortcuts);

/* ---- welcome back (patient) and record coverage (clinician) --------------------------- */
let coverageFor = null, coverage = null;
async function fetchCoverage() {
  if (!patient()) return null;
  try { coverage = await getJSON(`${base()}/coverage`); coverageFor = patient(); } catch { coverage = null; }
  return coverage;
}
const daysBetween = (a, b) => Math.round((new Date(b + "T00:00:00Z") - new Date(a + "T00:00:00Z")) / 86400000);
async function renderWelcomeBack() {
  const box = byId("welcome-back");
  const data = await fetchCoverage();
  const last = [data?.last_checkin_day, data?.last_medication_day].filter(Boolean).sort().pop();
  const away = data && last ? daysBetween(last, data.today) : 0;
  box.hidden = !(role() === "patient" && window.auraCompanionData?.safety_normal && away >= 7);
  if (!box.hidden) box.textContent = "Welcome back. You can carry on from today, or update past medication records if you'd like.";
}
async function loadCoverage() {
  const strip = byId("record-coverage");
  const data = await fetchCoverage();
  if (!data) { strip.hidden = true; return; }
  const day = iso => iso ? longDate(iso) : "none yet";
  strip.textContent = `Record coverage: last medication record ${day(data.last_medication_day)}` +
    `${data.reported_later_in_window ? ` (${data.reported_later_in_window} of the last ${data.window_days} days filled in later)` : ""}` +
    ` · last check-in ${day(data.last_checkin_day)} · latest watch data ${day(data.last_wearable_day)}.`;
  strip.hidden = false;
}
/* ---- "AURA agent live" light: which server answers (blue/green) and whether live AI is on ---- */
const NODE_NAMES = {blue: "blue", green: "green"};
async function checkAgent() {
  const light = byId("agent-live"), text = byId("agent-live-text");
  let health = null, status = null;
  try {
    const [h, s] = await Promise.all([fetch("/health", {cache: "no-store"}), fetch("/system/status", {cache: "no-store"})]);
    if (h.ok) health = await h.json();
    if (s.ok) status = await s.json();
  } catch { /* unreachable: shown as offline */ }
  const live = Boolean(health?.status === "ok" && status?.live_enabled);
  const node = NODE_NAMES[health?.node] || (health ? "other" : "none");
  light.dataset.state = live ? "live" : "offline";
  light.dataset.node = node;
  text.textContent = live ? "AURA agent live" : "AURA agent offline";
  byId("agent-live-short").textContent = live ? "Agent live" : "Agent offline";
  const where = health ? `Served by ${health.node}${health.node_label ? ` · ${health.node_label}` : ""}` : "Server not reachable";
  const ai = status ? (status.live_enabled ? `Live AI: ${status.provider} ${status.model}` : "Live AI is off; fixed wording is used") : "AI status unavailable";
  light.title = `${where}. ${ai}.`;
  light.setAttribute("aria-label", `${text.textContent}. ${where}.`);
}
checkAgent();
setInterval(checkAgent, 30000);
document.addEventListener("aura-settings-updated", checkAgent);
})();
