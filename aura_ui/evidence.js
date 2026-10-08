/* Read-only chart renderer. All statistics, findings and policy state are server facts. */
"use strict";
(() => {
  const node = (tag, text, className) => {
    const result = document.createElement(tag);
    if (text != null) result.textContent = text;
    if (className) result.className = className;
    return result;
  };
  const svgNode = (tag, attrs = {}, text) => {
    const result = document.createElementNS("http://www.w3.org/2000/svg", tag);
    for (const [key, value] of Object.entries(attrs)) result.setAttribute(key, value);
    if (text != null) result.textContent = text;
    return result;
  };
  const dayMs = 86400000;
  let lastEvidence=null, resizeTimer;
  const day = at => new Date(`${at.slice(0,10)}T00:00:00Z`).getTime();
  const shortDate = value => new Intl.DateTimeFormat("en-GB", {day:"numeric",month:"short",timeZone:"UTC"}).format(value);
  function valueLabel(value, signal) {
    if (value == null || !Number.isFinite(value)) return "Not available";
    if (signal.key.signal === "SLEEP_MIDPOINT") {
      const rounded = Math.round(value), clock = ((rounded % 1440) + 1440) % 1440;
      return `${String(Math.floor(clock/60)).padStart(2,"0")}:${String(clock%60).padStart(2,"0")} (${Math.floor(rounded/1440) >= 0 ? "+" : ""}${Math.floor(rounded/1440)}d)`;
    }
    return new Intl.NumberFormat("en-GB", {maximumFractionDigits:1}).format(value);
  }
  function drawChart(signal, start, end) {
    const card = node("section", null, "chart-card");
    card.dataset.signal = signal.key.signal;
    const heading = node("div", null, "chart-heading");
    heading.append(node("h2", signal.label), node("span", signal.key.signal === "SLEEP_MIDPOINT" ? "Source-local sleep clock" : signal.unit, "chart-unit"));
    card.append(heading);
    const current = signal.current;
    card.append(node("p", current ? `${current.sensing_state === "UNOBSERVED" ? "Data unavailable" : "Data observed"} · ${current.trust_state === "REESTABLISHING" ? "Reference being re-established" : current.trust_state === "TRUSTED" ? "Governed personal reference" : "Provisional reference"}` : "Current reference unavailable", "chart-status"));
    const inside = stamp => stamp >= start && stamp <= end;
    const raw = signal.observations.filter(row => inside(day(row.day)) && !row.deferred);
    // Last committed snapshot per record-date, for drawing only. Full snapshots stay in the API.
    const byDay = new Map();
    for (const row of signal.history) if (inside(day(row.at))) byDay.set(day(row.at), row);
    const history = [...byDay].sort((a,b) => a[0]-b[0]);
    const recordedDays = new Set(raw.map(row => day(row.day)));
    const values = raw.map(row => row.value);
    for (const [at,row] of history) if (recordedDays.has(at)) {
      if (row.rolling.sufficient && row.rolling.mean != null) values.push(row.rolling.mean);
      if (row.anchor) values.push(row.anchor.center);
    }
    const width=window.matchMedia("(max-width:700px)").matches ? 380 : 640;
    const chart = svgNode("svg", {viewBox:`0 0 ${width} 215`,role:"img","aria-label":`${signal.label}: recorded values, stored rolling mean and your own reference; missing days are gaps`});
    chart.append(svgNode("title", {}, signal.label), svgNode("desc", {}, "Descriptive synthetic records, not a normal range or clinical score. Exact records and sources are available below."));
    const low = values.length ? Math.min(...values) : 0, high = values.length ? Math.max(...values) : 1;
    const pad = Math.max((high-low)*.15, high === low ? Math.abs(high)*.03 : .1, .1);
    const bottom = low-pad, top = high+pad;
    const x = at => 66 + (width-90) * (at-start)/Math.max(dayMs,end-start);
    const y = value => 163 - 135 * (value-bottom)/(top-bottom);
    for (const value of [bottom,(bottom+top)/2,top]) {
      chart.append(svgNode("line",{x1:66,x2:width-24,y1:y(value),y2:y(value),class:"chart-grid"}),
        svgNode("text",{x:58,y:y(value)+4,"text-anchor":"end",class:"chart-axis"},signal.key.signal === "SLEEP_MIDPOINT" ? valueLabel(value,signal).split(" (")[0] : valueLabel(value,signal)));
    }
    for (const at of [start, start+(end-start)/2, end]) chart.append(svgNode("text",{x:x(at),y:193,"text-anchor":at===start?"start":at===end?"end":"middle",class:"chart-axis"},shortDate(at)));
    for (const context of signal.contexts) {
      const a = Math.max(start,day(context.start)), b = Math.min(end,context.end ? day(context.end) : end);
      if (a > b) continue;
      const band = svgNode("rect",{x:x(a),y:25,width:Math.max(2,x(b)-x(a)),height:140,class:context.category === "BENIGN_CONTEXT" ? "context-band" : "risk-context-band"});
      band.append(svgNode("title",{},`${context.explanation || "Reported context"}; applies only to linked signals; ${context.category}`));
      chart.append(band);
    }
    function lineSeries(kind) {
      let previous = null;
      for (const [at,row] of history) {
        const value = kind === "rolling" ? row.rolling.sufficient ? row.rolling.mean : null : row.anchor?.center;
        if (value == null || !recordedDays.has(at) || row.sensing_state === "UNOBSERVED") { previous=null; continue; }
        if (previous && at-previous.at <= dayMs && (kind !== "anchor" || previous.version === row.anchor?.version)) {
          chart.append(svgNode("line",{x1:x(previous.at),y1:y(previous.value),x2:x(at),y2:y(value),class:`chart-${kind}`}));
        } else chart.append(svgNode("circle",{cx:x(at),cy:y(value),r:2.4,class:`chart-${kind}-point`}));
        previous = {at,value,version:row.anchor?.version};
      }
    }
    lineSeries("anchor"); lineSeries("rolling");
    for (const row of raw) {
      const point = svgNode("circle",{cx:x(day(row.day)),cy:y(row.value),r:3,class:"chart-observed","data-event-id":row.event_id});
      point.append(svgNode("title",{},`${row.day}: ${valueLabel(row.value,signal)} · ${signal.unit} · reported coverage ${row.coverage}, data quality ${row.data_quality} · ${row.event_id}`)); chart.append(point);
    }
    if (!raw.length) chart.append(svgNode("text",{x:(width+42)/2,y:98,"text-anchor":"middle",class:"chart-empty"},"No observed values in these dates"));
    card.append(chart);
    if (current) {
      const availability = current.rolling.coverage_ratio;
      card.append(node("p",`Stored rolling-window data availability: ${availability == null ? "unavailable" : `${Math.round(availability*100)}%`} · ${current.rolling.sample_count} samples. Not chart-period coverage or a health score.`,"fine"));
      if (current.trust_state === "REESTABLISHING") card.append(node("p","Reference trust remains uncertain; no automatic exit rule is configured.","fine"));
    }
    const sources = node("details",null,"chart-sources"); sources.append(node("summary","Dates, sources & exact values"));
    sources.append(node("p",`Source: ${signal.key.source}${signal.key.metric ? ` · ${signal.key.metric}` : ""}. Values are unchanged from committed records. Rolling chart: last committed snapshot per record-date; insufficient windows are not plotted.`,"fine"));
    if (signal.key.signal === "SLEEP_MIDPOINT") sources.append(node("p","Sleep clock uses minutes from the source-local sleep-start midnight; +1d means the following day. No conversion to the viewer's timezone or circular re-analysis is performed.","fine"));
    const anchors = new Map();
    for (const row of signal.history) if (row.anchor) anchors.set(row.anchor.version,{...row.anchor,event_id:row.event_id});
    for (const anchor of anchors.values()) sources.append(node("p",`Your own reference v${anchor.version}: ${valueLabel(anchor.center,signal)} · reference ${anchor.reference_start} to ${anchor.reference_end} · created ${anchor.created_at}. Reviewer: ${anchor.reviewed_by || "not recorded"}.`,"fine"));
    const tableWrap = node("div",null,"table-scroll"), table = node("table");
    const caption = node("caption","Recorded observations in selected dates");
    const head = node("tr"); for (const label of ["Date","Value","Source event"]) { const th=node("th",label); th.scope="col"; head.append(th); }
    const thead=node("thead"); thead.append(head); table.append(caption,thead);
    const tbody=node("tbody");
    for (const row of raw) { const tr=node("tr"); tr.append(node("td",row.day),node("td",valueLabel(row.value,signal)),node("td",row.event_id)); tbody.append(tr); }
    table.append(tbody); tableWrap.append(table); sources.append(tableWrap); card.append(sources);
    return card;
  }

  window.renderAuraEvidence = evidence => {
    if (!evidence) return;
    lastEvidence=evidence;
    const recap = document.getElementById("month-recap");
    const hasRetained = evidence.signals.some(signal => signal.findings.length) || evidence.held.length;
    recap.hidden = !hasRetained;
    const mini = document.getElementById("recap-charts"); mini.replaceChildren();
    if (hasRetained && evidence.period.end) {
      const end = day(evidence.period.end);
      for (const signal of evidence.signals) mini.append(drawChart(signal, end - 29 * dayMs, end));
    }
    const byId = id => document.getElementById(id);
    byId("workspace-patient").textContent = `${evidence.patient.display_name} · ${evidence.patient.age} · ${evidence.patient.timezone} · ${evidence.patient.treatment?.medication_name || "Recorded treatment context"}`;
    const overview = byId("changes-overview"); overview.replaceChildren();
    // One latest descriptive finding per signal, in the server's fixed signal order.
    // This is display selection by date, not severity ranking or a new drift decision.
    const findings = evidence.signals.flatMap(signal => signal.findings.length ?
      [signal.findings.reduce((latest,row) => day(row.last_seen) > day(latest.last_seen) ? row : latest)] : []);
    for (const finding of findings.slice(0,3)) {
      const text = node("p",`${finding.drift.description.replace(/\.$/,"")} — recorded ${shortDate(day(finding.first_seen))}–${shortDate(day(finding.last_seen))}.`);
      const detail = node("details",null,"finding-source"); detail.append(node("summary","Source & context"),node("p",`${finding.drift.key.source} · latest event ${finding.event_id}. ${finding.drift.attenuated ? "Linked benign context attenuates this observation only." : "No benign attenuation recorded for this finding."}`,"fine"));
      const section=node("section"); section.append(text,detail); overview.append(section);
    }
    if (!findings.length) overview.append(node("p","No descriptive change is retained in these records. This is not an assessment of mental health."));
    byId("workspace-decision").textContent = `Current communication: ${evidence.current_decision === "STAY_QUIET" ? "no question pending" : evidence.current_decision === "SAFETY_REVIEW_REQUIRED" ? "safety policy takes priority" : "an approved interaction is available in Patient view"}. Retained changes are history, not a new prompt.`;
    const charts = byId("evidence-charts"); charts.replaceChildren();
    if (evidence.period.end && evidence.period.start) {
      const end = day(evidence.period.end), allStart = day(evidence.period.start);
      const start = byId("chart-range").value === "all" ? allStart : Math.max(allStart,end-55*dayMs);
      for (const signal of evidence.signals) charts.append(drawChart(signal,start,end));
    } else charts.append(node("p","No recorded history yet."));
    const strip = byId("evidence-strip"); strip.replaceChildren();
    for (const [title,rows,field] of [["Check-ins · patient reports",evidence.checkins,"state"],["Medication routine · not verified ingestion",evidence.medication,"status"]]) {
      const section=node("section"), details=node("details"), summary=node("summary",`${title} · ${rows.length} records`), entries=node("div",null,"categorical-strip");
      const end=evidence.period.end ? day(evidence.period.end) : 0;
      const start=byId("chart-range").value === "all" ? -Infinity : end-55*dayMs;
      const visibleRows=rows.filter(row=>day(row.at)>=start && day(row.at)<=end);
      const preview=node("div",null,"categorical-strip reports-preview");
      preview.append(node("span",`${title} · latest ${Math.min(7,visibleRows.length)} in chart dates`,"fine"));
      for (const row of visibleRows.slice(-7)) preview.append(node("span",`${shortDate(day(row.at))} · ${row[field]}${row.deferred ? " · held" : ""}`,"report-dot"));
      if(!visibleRows.length) preview.append(node("span","None recorded in chart dates", "fine"));
      for (const row of visibleRows) {
        const entry=node("span",`${shortDate(day(row.at))} · ${row[field]}${row.deferred ? " · held pending safety evaluation" : ""}`,"report-dot");
        entry.title=`Source event: ${row.event_id}`; entries.append(entry);
      }
      details.append(summary,entries); section.append(preview,details); strip.append(section);
    }
    const safety=byId("safety-evidence"); safety.replaceChildren();
    for (const ref of evidence.safety.references) safety.append(node("p",`${ref.at || "Date unavailable"} · episode ${ref.episode_id || "none — degraded overlay"} · ${ref.state.episode_status} · sequence ${ref.sequence} · ${ref.state.degraded ? "degraded" : "not degraded"} · source episode ${ref.source_episode_id || "none"} · previous episode ${ref.previous_episode_id || "none"}. Source event: ${ref.event_id}.`,"fine"));
    if (!evidence.safety.references.length) safety.append(node("p","No safety episode references recorded. This is not a determination of safety."));
    safety.append(node("p","No clinician or emergency service is automatically notified. Current policy output and separate resources stay outside this history section.","fine"));
    byId("workspace-safety").open = Boolean(evidence.safety.state?.episode_id || evidence.safety.state?.degraded);
    const review=byId("evidence-review"); review.replaceChildren();
    const treatment=evidence.patient.treatment||{};
    review.append(node("p",`Recorded treatment context: ${treatment.medication_name || "not recorded"} · schedule ${treatment.medication_schedule || "not recorded"} · stable since ${treatment.stable_since || "not recorded"} · next review ${treatment.next_review || "not configured"}. These are records, not treatment instructions.`,"fine"));
    for(const row of evidence.questions) review.append(node("p",`${row.question} · ${shortDate(day(row.at))}`,"fine"));
    if(!evidence.questions.length)review.append(node("p","No patient-selected questions recorded.","fine"));
    for(const row of evidence.review_items)review.append(node("p",`${row.summary} · ${row.status} · not shared`,"fine"));
    if(!evidence.review_items.length)review.append(node("p","No review items prepared.","fine"));
    byId("workspace-review").open=Boolean(evidence.questions.length);
  };
  window.addEventListener("resize",()=>{
    clearTimeout(resizeTimer);
    resizeTimer=setTimeout(()=>{if(lastEvidence)window.renderAuraEvidence(lastEvidence);},100);
  });
})();
