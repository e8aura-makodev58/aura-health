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
  prep.append(node("h2", "Draft from the recorded context"), node("p", "Remove any line you do not want. Not sent.", "fine"));
  const button = node("button", "Help prepare my note"); button.dataset.agentRole = "visit_prep";
  const output = node("div"); output.id = "agent-visit_prep"; output.setAttribute("aria-live", "polite");
  prep.append(button, output); preview.before(prep);

  function render(result, area, role) {
    area.replaceChildren();
    const mixed=result.reason==='VALIDATED_PARTIAL_MODEL_DRAFT';
    const chip=node('details',null,'agent-disclosure');chip.append(node('summary',mixed&&result.extracted_fact_ids?.length?'Checked AI + source extraction':result.generation_used?'AI-written · sources checked':'Offline extraction'),node('p',result.disclosure,'fine'));area.append(chip);
    if(result.draft.headline)area.append(node('h3',result.draft.headline));
    let previousSection=null;
    for (const claim of result.draft.claims) {
      const section=claim.section||'changes';
      if(section!==previousSection){area.append(node('h4',({changes:'What changed',context:'Context recorded',gaps:'Data gaps',routine:'Routine',review:'For review'})[section]));previousSection=section;}
      const line = node("section", null, "agent-claim");
      line.append(node("p", claim.text));
      if(claim.fact_ids.some(id=>(result.extracted_fact_ids||[]).includes(id)))line.append(node('span','Source extraction','fine'));
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
    for (const entry of result.trace) trace.append(node("p", entry.tool ? `${entry.tool}: ${(entry.fact_ids||[]).length} linked facts${entry.code?' · '+entry.code:''}` : `${entry.action}: ${entry.result || entry.reason || "bounded model request"}`, "fine"));
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
          query_id: role === "record_qa" && !document.getElementById('agent-question-text')?.value.trim() ? document.getElementById("agent-query").value : null,
          question: role==='record_qa' ? document.getElementById('agent-question-text')?.value.trim()||null:null, client_offline: false})
      });
      const result = await response.json();
      const latest = window.auraAgentContext();
      if (ticket !== requestEpoch || latest.patientId !== originalPatient || latest.offline) return;
      if (!response.ok) throw new Error(result.error?.message || "Assistant could not complete the request.");
      if(role==='record_qa' && document.getElementById('agent-question-text')?.value.trim())await refresh();
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
