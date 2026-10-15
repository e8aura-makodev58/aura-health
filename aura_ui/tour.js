/* Guided story: one person's day, one highlighted thing, one Next button.
   Uses the app's real actions and waits for their real results. Back never repeats an action.
   Help and safety always stay visible and clickable; safety pauses the tour. */
"use strict";
(function () {
  const $ = id => document.getElementById(id);
  const QUESTION = "When did sleep timing change, and was anything reported around then?";
  const CATCH_UP = "I took it on most days except last Friday and yesterday";
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
    {chapter: "Your day", title: "Missed a few days? Just say so", text: `The patient writes: "${CATCH_UP}"`,
     enter: async () => { patientHome(); await wait(() => visible($("dose-card")), 20000); },
     target: () => visible($("calendar-view")) ? $("calendar-grid") : visible($("med-update-line")) ? $("med-update-line") : $("dose-card"),
     action: async run => {
       const live = () => tour && tour.run === run;
       $("med-update-open").click();
       if (!await wait(() => $("med-update-dialog").open, 15000, run)) return live() ? "This isn't available just now. You can still continue." : "";
       await pause(900); if (!live()) return "";
       $("med-update-text").value = CATCH_UP;
       await pause(1600); if (!live()) return "";
       $("med-update-interpret").click();
       // AURA reads the sentence (about 10 seconds live); if it can't, the days are tapped instead.
       await wait(() => !$("med-update-preview").hidden || (!$("med-update-interpret").disabled && !/reading that/.test($("med-update-message").textContent)), 60000, run);
       if (!live()) return "";
       const typed = !$("med-update-preview").hidden && Boolean(document.querySelector('#med-update-preview .med-day[data-basis="explicit"], #med-update-preview .med-day[data-basis="from_most_days"]'));
       if (typed) {
         await pause(2600); if (!live()) return "";
         if (visible($("med-update-question"))) { $("med-update-yes").click(); await pause(1500); }
       } else {
         $("med-update-tap").click(); await pause(900);
         const open = [...document.querySelectorAll('#med-update-preview .med-day[data-locked="false"]')].slice(-2).map(day => day.dataset.date);
         const tap = date => document.querySelector(`#med-update-preview .med-day[data-date="${date}"]`)?.click();
         if (open[0]) tap(open[0]);
         if (open[1]) { tap(open[1]); await pause(400); tap(open[1]); }
         await pause(1500);
       }
       if (!live()) return "";
       $("med-update-save").click();
       await wait(() => !$("med-update-result").hidden, 20000, run);
       if (!live()) return "";
       const saved = /^Saved/.test($("med-update-result").textContent);
       await pause(1800); if (!live()) return "";
       $("med-update-dialog").close();
       if (!saved) return "This couldn't be saved just now. You can still continue.";
       location.hash = "calendar";
       await wait(() => document.querySelector('#calendar-grid .cal-med[data-reported-later="true"]'), 15000, run);
       return typed ? "AURA turned the sentence into days, asked one question, and saved them. Ringed marks mean filled in later."
                    : "Saved by tapping the days. Ringed marks mean filled in later.";
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
       $("agent-record_qa").replaceChildren(); // wait for this answer, not an earlier one
       document.querySelector(".question-submit")?.click();
       const done = await wait(() => document.querySelector("#agent-record_qa .investigation-trail, #agent-record_qa .agent-claim")
         || /unavailable|could not|paused/i.test($("agent-record_qa")?.textContent || ""), 120000, run);
       if (!done) return "AURA couldn't complete this answer in time. You can still continue.";
       const checked = /AI-written/.test(document.querySelector("#agent-record_qa .agent-disclosure")?.textContent || "");
       if (checked) return "It chose what to read, then a second check reviewed every statement. See How AURA looked.";
       tour.retry = true; // visible, user-chosen retry only; never automatic
       return "AURA couldn't complete this answer; here are the related records it found. You can ask again, or continue.";
     }},
    {chapter: "When things change", title: "When life changes", text: "Three days of flu, simulated. AURA describes what changed in this person's own records.",
     enter: async () => { patientHome(); await wait(() => visible($("month-recap")), 20000); },
     target: () => visible($("suggestion-card")) && tour?.done.has(STEPS.length - 1) ? $("suggestion-card") : $("month-recap"),
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

  // The safety example keeps the card open: it explains why the panel stays and offers a way out.
  async function showSafety() {
    if (!tour) return;
    const run = tour.run;
    tour.index = STEPS.length + 1; spotlight(null); render("finish");
    const {ui} = tour, actions = ui.card.querySelector(".tour-actions");
    ui.chapter.textContent = "Safety example";
    ui.title.textContent = "Sending a worrying message…";
    ui.text.textContent = "AURA picks an example message that sounds unsafe (masked here), so you can see what happens.";
    ui.status.textContent = ""; actions.replaceChildren();
    patientHome();
    await pause(800);
    // Paced so the visitor sees the note box, the chosen example and the send.
    $("talk").click();
    await pause(1800);
    if (!tour || tour.run !== run) return;
    document.querySelector('[data-fixture="fixture safety concern"]')?.click();
    await pause(3500);
    if (!tour || tour.run !== run) return;
    $("send-input")?.focus();
    await pause(1200);
    if (!tour || tour.run !== run) return;
    $("send-input")?.click();
    for (let waited = 0; waited < 30000 && $("safety-panel").hidden; waited += 250) await pause(250);
    if (!tour || tour.run !== run) return;
    ui.title.textContent = "Safety takes priority";
    ui.text.textContent = "When a message may mean someone is unsafe, AURA sets everything else aside and shows safety contacts. The patient can't dismiss it, and the clinician sees it when they open the record. This prototype doesn't send alerts. In this demo, you can reset to start fresh.";
    const reset = el("button", "tour-next primary", "Reset the demo");
    reset.addEventListener("click", async () => { reset.disabled = true; ui.status.textContent = "Resetting…"; await freshDemo(); stop(); window.scrollTo(0, 0); });
    const explore = el("button", "tour-back", "Keep exploring"); explore.addEventListener("click", stop);
    actions.append(explore, reset); reset.focus();
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
    ui.card.querySelector(".tour-retry")?.remove(); tour.retry = false;
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
    showRetry(index, run);
    ui.next.disabled = false; ui.next.focus({preventScroll: true});
  }

  function showRetry(index, run) {
    tour.ui.card.querySelector(".tour-retry")?.remove();
    if (!tour.retry || !STEPS[index].action) return;
    tour.retry = false;
    const again = el("button", "tour-retry", "Ask again");
    again.addEventListener("click", async () => {
      again.disabled = true; tour.ui.next.disabled = true; tour.ui.status.textContent = "Asking again…";
      let message;
      try { message = await STEPS[index].action(run); } catch { message = "This part isn't available just now. You can still continue."; }
      if (!tour || tour.run !== run || tour.index !== index) return;
      tour.messages[index] = message; tour.ui.status.textContent = message; again.remove();
      showRetry(index, run); spotlight(STEPS[index].target()); tour.ui.next.disabled = false;
    });
    tour.ui.card.querySelector(".tour-actions").prepend(again);
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
  window.auraTour = {start, stop, active: () => Boolean(tour), step: () => tour?.index ?? null, finishForTest: () => tour && showFinish()};
})();
