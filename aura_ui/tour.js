/* Guided story: one person's day, one highlighted thing, one Next button.
   Uses the app's real actions and waits for their real results. Back never repeats an action.
   Help and safety always stay visible and clickable; safety pauses the tour. */
"use strict";
(function () {
  const $ = id => document.getElementById(id);
  const QUESTION = "When did sleep timing change, and was anything reported around then?";
  const MED_QUESTION = "Can I take ibuprofen with it?";
  let tour = null; // {run, index, done:Set, card, hole}

  const visible = el => Boolean(el && el.offsetParent !== null && !el.hidden);
  const wait = (test, ms = 30000, run) => new Promise(resolve => {
    const start = Date.now();
    const tick = () => {
      if (!tour || (run && tour.run !== run)) return resolve(false);
      let ok = false; try { ok = test(); } catch { ok = false; }
      if (ok) return resolve(true);
      if (Date.now() - start > ms) return resolve(false);
      setTimeout(tick, 200);
    };
    tick();
  });
  const pause = ms => new Promise(r => setTimeout(r, ms));
  const patientHome = () => { $("patient-role").click(); location.hash = "home"; };
  const record = () => window.auraAgentContext?.() || {};

  // Each step: where to look, what it means, and (optionally) one real action whose result we wait for.
  const STEPS = [
    {chapter: "Your day", title: "Every day starts with a breath", text: "No dashboard, no scores. Just a calm start.",
     enter: async () => { patientHome(); await wait(() => visible($("home-view"))); },
     target: () => visible($("breath-welcome")) ? $("breath-welcome") : $("home-heading"),
     leave: () => { if (visible($("breath-welcome"))) $("breath-continue").click(); }},
    {chapter: "Your day", title: "One short summary", text: "Written by AI from checked facts, and compared with this person's own usual.",
     enter: async () => { patientHome(); await wait(() => document.querySelector(".patient-recap"), 45000); },
     target: () => $("month-recap")},
    {chapter: "Your day", title: "One tap for today's dose", text: "In this example, the patient skipped a dose because of side effects.",
     enter: async () => { patientHome(); await wait(() => visible($("dose-card")), 20000); },
     target: () => $("dose-card"),
     action: async run => {
       $("dose-card").querySelector(".dose-skipped")?.click();
       await wait(() => visible($("dose-reason")), 5000, run);
       document.querySelector('[data-reason="SIDE_EFFECTS"]')?.click();
       const saved = await wait(() => /Recorded/.test($("dose-saved")?.textContent || ""), 20000, run);
       return saved ? "Saved: skipped, because of side effects." : "This couldn't be saved just now. You can still continue.";
     }},
    {chapter: "Your day", title: "Plain answers about the medication", text: "From approved information about this person's own prescription.",
     enter: async () => { patientHome(); await wait(() => visible($("medication-card")), 20000); },
     target: () => $("medication-card"),
     action: async run => {
       document.querySelector('.topic-chip[data-topic-id="missed_dose"]')?.click();
       const shown = await wait(() => !$("medication-answer").hidden && $("answer-text").textContent.trim(), 20000, run);
       return shown ? "This is what the leaflet says about a missed dose." : "The answer isn't available just now. You can still continue.";
     }},
    {chapter: "Your day", title: "Honest when it can't answer", text: `Asked: "${MED_QUESTION}"`,
     enter: async () => { patientHome(); await wait(() => visible($("medication-card")), 20000); },
     target: () => $("medication-card"),
     action: async run => {
       const details = document.querySelector(".medication-ask"); if (details) details.open = true;
       $("medication-question").value = MED_QUESTION;
       $("answer-text").textContent = "";
       $("medication-ask-btn").click();
       const shown = await wait(() => !$("medication-answer").hidden && $("answer-text").textContent.trim(), 30000, run);
       return shown ? "AURA says it can't identify that medication, and points to the pharmacist." : "The answer isn't available just now. You can still continue.";
     }},
    {chapter: "Getting ready for a visit", title: "Ready for the appointment", text: "The skipped dose and its reason are ready to discuss. Nothing is sent until the patient decides.",
     enter: async () => { $("patient-role").click(); location.hash = "review"; await wait(() => visible($("review-view")), 10000); await pause(600); },
     target: () => visible($("missed-dose-items")) ? $("missed-dose-items") : $("appointment-preview")},
    {chapter: "Getting ready for a visit", title: "Now, the clinician's view of this demo record", text: "What changed and when, with exact values and sources.",
     enter: async () => { $("clinician-role").click(); await wait(() => document.querySelector("#agent-clinician_brief .clinician-finding"), 45000); },
     target: () => $("agent-clinician_brief")},
    {chapter: "Getting ready for a visit", title: "The AI agent investigates", text: `The clinician asks: "${QUESTION}"`,
     enter: async () => { $("clinician-role").click(); await wait(() => visible($("agent-question-text")), 20000); },
     target: () => document.querySelector(".record-questions") || $("agent-record_qa"),
     action: async run => {
       $("agent-question-text").value = QUESTION;
       document.querySelector(".question-submit")?.click();
       const done = await wait(() => document.querySelector("#agent-record_qa .investigation-trail, #agent-record_qa .agent-claim")
         || /unavailable|could not|paused/i.test($("agent-record_qa")?.textContent || ""), 120000, run);
       if (!done) return "AURA couldn't complete this answer in time. You can still continue.";
       const checked = /AI-written/.test(document.querySelector("#agent-record_qa .agent-disclosure")?.textContent || "");
       return checked ? "It chose what to read, then a second check reviewed every statement. See How AURA looked."
                      : "AURA couldn't complete this answer; here are the related records it found.";
     }},
    {chapter: "When things change", title: "When life changes", text: "Three days of flu, simulated. AURA describes what changed in this person's own records.",
     enter: async () => { patientHome(); await wait(() => visible($("month-recap")), 20000); },
     target: () => visible($("suggestion-card")) && tour?.done.has(8) ? $("suggestion-card") : $("month-recap"),
     action: async run => {
       const id = record().patientId;
       const response = await fetch(`/patients/${encodeURIComponent(id)}/workflows/advance`, {method: "POST", headers: {"Content-Type": "application/json"},
         body: JSON.stringify({run_id: window.auraUniqueId(), data: {days: 3, seed: 7, request: "Flu", notes: false}})});
       if (!tour || tour.run !== run) return "";
       if (!response.ok) return "The simulation isn't available just now. You can still continue.";
       if (typeof refresh === "function") await refresh();
       window.dispatchEvent(new CustomEvent("aura-input-committed"));
       await wait(() => !document.querySelector(".recap-pending"), 60000, run);
       return visible($("suggestion-card")) ? "The summary now reflects the flu, with a small, optional idea for today."
                                            : "The summary now reflects the flu.";
     }},
  ];

  function el(tag, cls, text) { const n = document.createElement(tag); if (cls) n.className = cls; if (text != null) n.textContent = text; return n; }

  function buildCard() {
    const card = el("section", "tour-card"); card.setAttribute("role", "dialog"); card.setAttribute("aria-live", "polite"); card.setAttribute("aria-label", "Guided story");
    const top = el("div", "tour-top"); const chapter = el("span", "tour-chapter"); const exit = el("button", "tour-exit", "×");
    exit.setAttribute("aria-label", "Exit the guided story"); exit.addEventListener("click", stop); top.append(chapter, exit);
    const dots = el("div", "tour-dots"); dots.setAttribute("aria-hidden", "true");
    const title = el("h2", "tour-title"); const text = el("p", "tour-text"); const status = el("p", "tour-status");
    const actions = el("div", "tour-actions"); const back = el("button", "tour-back", "Back"); const next = el("button", "tour-next primary", "Next →");
    back.addEventListener("click", () => go(tour.index - 1)); next.addEventListener("click", onNext); actions.append(back, next);
    card.append(top, dots, title, text, status, actions);
    return {card, chapter, dots, title, text, status, back, next};
  }

  function render(state) {
    const {ui} = tour;
    ui.card.classList.toggle("tour-intro", state === "intro" || state === "finish");
    ui.dots.replaceChildren(...STEPS.map((_, i) => { const d = el("span", i === tour.index ? "on" : i < tour.index ? "past" : ""); return d; }));
    ui.dots.hidden = state !== "step";
    ui.back.hidden = state !== "step" || tour.index === 0;
  }

  function showIntro() {
    tour.index = -1; spotlight(null); render("intro");
    const {ui} = tour;
    ui.chapter.textContent = "Guided story · about 3 minutes";
    ui.title.textContent = "See how AURA helps, through one person's day";
    ui.text.textContent = "Press Next to move on. AURA does the tapping for you. This starts a fresh demo, so any changes you made here are cleared.";
    ui.status.textContent = "";
    ui.next.textContent = "Start"; ui.next.disabled = false; ui.next.focus();
  }

  function showFinish() {
    tour.index = STEPS.length; spotlight(null); render("finish");
    const {ui} = tour;
    ui.chapter.textContent = "That's AURA";
    ui.title.textContent = "A calm companion between doctor visits";
    ui.text.textContent = "One more thing: anything a patient types is safety-checked first. You can see that now, explore on your own, or start again.";
    ui.status.textContent = "";
    const actions = ui.card.querySelector(".tour-actions"); actions.replaceChildren();
    const safety = el("button", "tour-back", "Show the safety example"); safety.addEventListener("click", showSafety);
    const explore = el("button", "tour-back", "Explore on my own"); explore.addEventListener("click", stop);
    const again = el("button", "tour-next primary", "Start again"); again.addEventListener("click", () => { stop(); start(); });
    actions.append(safety, explore, again); again.focus();
  }

  async function showSafety() {
    stop();
    patientHome();
    await pause(500);
    $("talk").click();
    await pause(300);
    document.querySelector('[data-fixture="fixture safety concern"]')?.click();
    await pause(200);
    $("send-input")?.click();
  }

  async function freshDemo() {
    try {
      const reset = await fetch("/demo/reset", {method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify({confirm: "RESET_SYNTHETIC_SESSION"})});
      void reset;
    } catch { /* local development: no reset route */ }
    try { sessionStorage.removeItem("aura-welcomed"); } catch { /* storage unavailable */ }
    const patient = (typeof catalog !== "undefined" && catalog.find(row => row.id === "B")) || null;
    if (patient && typeof loadPatient === "function") { $("scenario").value = patient.patient_id; await loadPatient(patient.patient_id); }
  }

  async function onNext() {
    if (!tour) return;
    if (tour.index === -1) {
      tour.ui.next.disabled = true; tour.ui.status.textContent = "Preparing a fresh demo…";
      const run = tour.run; await freshDemo(); if (!tour || tour.run !== run) return;
      return go(0);
    }
    const step = STEPS[tour.index];
    if (step?.leave) step.leave();
    return go(tour.index + 1);
  }

  async function go(index) {
    if (!tour) return;
    if (index < 0) return showIntro();
    if (index >= STEPS.length) return showFinish();
    const run = tour.run; tour.index = index; render("step");
    const step = STEPS[index], {ui} = tour;
    ui.chapter.textContent = `${step.chapter} · ${index + 1} of ${STEPS.length}`;
    ui.title.textContent = step.title; ui.text.textContent = step.text;
    ui.status.textContent = ""; ui.next.textContent = index === STEPS.length - 1 ? "Finish" : "Next →"; ui.next.disabled = true;
    try { await step.enter(); } catch { /* still show the step */ }
    if (!tour || tour.run !== run || tour.index !== index) return;
    spotlight(step.target());
    if (step.action && !tour.done.has(index)) {
      tour.done.add(index); // Back and double taps never repeat a real action.
      ui.status.textContent = "Working…";
      let message;
      try { message = await step.action(run); } catch { message = "This part isn't available just now. You can still continue."; }
      if (!tour || tour.run !== run || tour.index !== index) return;
      tour.messages[index] = message;
      spotlight(step.target());
    }
    ui.status.textContent = tour.messages[index] || "";
    ui.next.disabled = false; ui.next.focus({preventScroll: true});
  }

  // Spotlight: a static outline around the target and a gentle dimming everywhere else.
  function spotlight(target) {
    tour.target = target || null;
    if (target) {
      const rect = target.getBoundingClientRect();
      const cardTop = tour.ui.card.getBoundingClientRect().top;
      const room = Math.max(120, cardTop - 80);
      if (rect.top < 70 || rect.top > room - 40) window.scrollBy({top: rect.top - 90, behavior: "smooth"});
    }
    place();
  }

  function place() {
    if (!tour) return;
    const hole = tour.hole, target = tour.target;
    if (!target || !visible(target)) { hole.hidden = true; return; }
    const r = target.getBoundingClientRect(), pad = 8;
    Object.assign(hole.style, {left: `${r.left - pad}px`, top: `${r.top - pad}px`, width: `${r.width + pad * 2}px`, height: `${r.height + pad * 2}px`});
    hole.hidden = false;
  }

  function loop() {
    if (!tour) return;
    place();
    // Safety always comes first: if the safety panel appears, the ordinary tour steps aside.
    if (!$("safety-panel").hidden && tour.index >= 0 && tour.index < STEPS.length) {
      tour.ui.title.textContent = "Safety comes first";
      tour.ui.text.textContent = "The safety panel takes priority, so the guided story has paused.";
      tour.ui.status.textContent = ""; tour.ui.next.disabled = true; tour.hole.hidden = true; tour.target = null;
    }
    tour.frame = requestAnimationFrame(loop);
  }

  function start() {
    if (tour) stop();
    $("demo-panel").hidden = true; $("demo-toggle")?.setAttribute("aria-expanded", "false");
    const ui = buildCard(), hole = el("div", "tour-hole"); hole.hidden = true; hole.setAttribute("aria-hidden", "true");
    document.body.append(hole, ui.card); document.body.classList.add("touring");
    tour = {run: Date.now() + Math.random(), index: -1, done: new Set(), messages: {}, ui, hole, target: null, frame: 0};
    showIntro(); loop();
  }

  function stop() {
    if (!tour) return;
    cancelAnimationFrame(tour.frame);
    tour.ui.card.remove(); tour.hole.remove(); document.body.classList.remove("touring");
    tour = null;
  }

  document.addEventListener("keydown", event => { if (tour && event.key === "Escape") stop(); });
  window.auraTour = {start, stop, active: () => Boolean(tour), step: () => tour?.index ?? null};
})();
