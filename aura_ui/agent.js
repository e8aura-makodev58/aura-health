/* Read-only agent UI. No safety/drift decisions or free-text model input. */
"use strict";
(() => {
  const node = (tag, text, className) => {
    const el = document.createElement(tag);
    if (text != null) el.textContent = text;
    if (className) el.className = className;
    return el;
  };
  let identity = null, requestEpoch = 0;
  const preview = document.getElementById("appointment-preview");
  const prep = node("section", null, "card agent-card");
  prep.append(node("h2", "Draft from the recorded context"), node("p", "Optional assistant draft. Remove any line you do not want in this temporary preview. Nothing is saved as approval or sent.", "fine"));
  const button = node("button", "Help prepare my note"); button.dataset.agentRole = "visit_prep";
  const output = node("div"); output.id = "agent-visit_prep"; output.setAttribute("aria-live", "polite");
  prep.append(button, output); preview.before(prep);

  function render(result, area, role) {
    area.replaceChildren();
    area.append(node("p", result.disclosure, "fine agent-disclosure"));
    for (const claim of result.draft.claims) {
      const line = node("section", null, "agent-claim");
      line.append(node("p", claim.text));
      const sources = node("details"); sources.append(node("summary", "Show sources"));
      for (const id of claim.fact_ids) {
        const fact = result.sources.find(row => row.fact_id === id);
        if (fact) sources.append(node("p", `${fact.text} Source: ${fact.source_ref}.`, "fine"));
      }
      line.append(sources);
      if (role === "visit_prep") {
        const remove = node("button", "Remove from this preview", "text-button");
        remove.addEventListener("click", () => line.remove()); line.append(remove);
      }
      area.append(line);
    }
    for (const id of result.draft.question_ids) {
      area.append(node("p", result.question_options[id], "agent-question"));
    }
    if (!result.draft.claims.length && !result.draft.question_ids.length && result.status === "COMPLETE") {
      area.append(node("p", "No additional answer or question was established from the available record."));
    }
    const trace = node("details", null, "agent-trace");
    trace.append(node("summary", "Inspect assistant steps · synthetic demo"),
      node("p", `Run ${result.run_id} · ${result.model_id || "not called"} · ${result.reason || result.status} · ${result.elapsed_ms || 0} ms`, "fine"));
    for (const entry of result.trace) trace.append(node("p", entry.tool ? `${entry.tool}: ${entry.fact_ids.length} linked facts` : `${entry.action}: ${entry.result || entry.reason || "bounded model request"}`, "fine"));
    area.append(trace);
  }

  document.addEventListener("click", async event => {
    const trigger = event.target.closest("[data-agent-role]");
    if (!trigger) return;
    const context = window.auraAgentContext();
    const role = trigger.dataset.agentRole, area = document.getElementById(`agent-${role}`);
    if (!context.patientId || context.offline || !navigator.onLine) {
      area.replaceChildren(node("p", "Assistant unavailable while offline or input is pending. Safety resources remain separate.")); return;
    }
    const ticket = requestEpoch, originalPatient = context.patientId, revision = context.revision;
    trigger.disabled = true; area.replaceChildren(node("p", "Reading the recorded evidence…"));
    try {
      const response = await fetch(`/patients/${encodeURIComponent(context.patientId)}/agent/${role}`, {
        method: "POST", headers: {"Content-Type": "application/json"}, cache: "no-store",
        body: JSON.stringify({run_id: window.auraUniqueId(), window_days: role === "patient_insight" ? 30 : 56,
          query_id: role === "record_qa" ? document.getElementById("agent-query").value : null, client_offline: false})
      });
      const result = await response.json();
      const latest = window.auraAgentContext();
      if (ticket !== requestEpoch || latest.patientId !== originalPatient || latest.revision !== revision || latest.offline) return;
      if (!response.ok) throw new Error(result.error?.message || "Assistant could not complete the request.");
      render(result, area, role);
    } catch (error) {
      if (ticket === requestEpoch) area.replaceChildren(node("p", error.message || "Assistant unavailable. Your records and safety policy are unchanged."));
    } finally { trigger.disabled = false; }
  });

  window.addEventListener("aura-record-view", () => {
    const context = window.auraAgentContext();
    const key = `${context.patientId}:${context.revision}:${context.offline}`;
    if (key !== identity) {
      identity = key; requestEpoch++;
      for (const area of document.querySelectorAll('[id^="agent-"]')) if (area.id !== "agent-workspace" && area.id !== "agent-query") area.replaceChildren();
    }
    for (const trigger of document.querySelectorAll("[data-agent-role]")) trigger.disabled = context.offline;
  });
})();
