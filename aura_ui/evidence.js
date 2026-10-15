/* Read-only chart renderer. All statistics, findings and policy state are server facts. */
"use strict";
(() => {
  const node = (tag, text, className) => {
    const result = document.createElement(tag);
    if (text != null) result.textContent = window.auraPlain(text);
    if (className) result.className = className;
    return result;
  };
  const svgNode = (tag, attrs = {}, text) => {
    const result = document.createElementNS("http://www.w3.org/2000/svg", tag);
    for (const [key, value] of Object.entries(attrs)) result.setAttribute(key, key==='aria-label'?window.auraPlain(value):value);
    if (text != null) result.textContent = window.auraPlain(text);
    return result;
  };
  const dayMs = 86400000;
  let lastEvidence=null, resizeTimer, storyItems=[], storySources=[], comparisonOpen=false, comparisonAssessment=null;
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
  const keyOf = key => JSON.stringify([key.signal,key.source,key.metric||""]);
  const chartId = key => `chart-${encodeURIComponent(keyOf(key)).replaceAll('%','_')}`;
  function revealChart(target) {
    for(let parent=target.parentElement;parent;parent=parent.parentElement)if(parent.tagName==='DETAILS')parent.open=true;
    target.scrollIntoView({block:'center',behavior:'auto'});target.focus({preventScroll:true});
  }
  function storyFor(signal) {
    return storyItems.flatMap(item => {
      const source=storySources.find(row=>row.fact_id===item.fact_id);
      const candidates=lastEvidence.signals.flatMap(channel=>channel.findings.map(finding=>({channel,finding})))
        .filter(({channel,finding})=>channel.key.signal===item.signal && finding.first_seen.slice(0,10)===item.since?.slice(0,10)
          && (!source?.source_ref || finding.event_id===source.source_ref)
          && (!item.source || channel.key.source===item.source)
          && (!item.metric || channel.key.metric===item.metric));
      if(candidates.length!==1 || keyOf(candidates[0].channel.key)!==keyOf(signal.key))return [];
      return [{...item,until:candidates[0].finding.last_seen, target_id:item.target_id||`story-finding-${item.number}`}];
    });
  }
  function drawCheckins(start,end,width) {
    const svg=svgNode('svg',{viewBox:`0 0 ${width} 70`,role:'img','aria-label':'Patient check-ins on the same dates as the chart; separate categorical reports, not a trend',class:'aligned-checkins'});
    const x=at=>66+(width-90)*(at-start)/Math.max(dayMs,end-start);
    const states=['Good','Okay','Rough'];
    states.forEach((state,index)=>svg.append(svgNode('text',{x:58,y:15+index*19,'text-anchor':'end',class:'chart-axis'},state)));
    for(const row of lastEvidence.checkins) {
      const at=day(row.at),index=states.indexOf(row.state);
      if(at<start||at>end||index<0||row.deferred)continue;
      const point=svgNode('circle',{cx:x(at),cy:11+index*19,r:3,class:`checkin-point checkin-${row.state.toLowerCase()}`,'data-event-id':row.event_id});
      point.append(svgNode('title',{},`${shortDate(day(row.at))} · ${row.state} · your check-in`));svg.append(point);
    }
    return svg;
  }
  function drawChart(signal, start, end) {
    const card = node("section", null, "chart-card");
    card.dataset.signal = signal.key.signal;
    card.id=chartId(signal.key);card.tabIndex=-1;card.dataset.source=signal.key.source;card.dataset.metric=signal.key.metric||'';
    const heading = node("div", null, "chart-heading");
    heading.append(node("h2", signal.label), node("span", signal.key.signal === "SLEEP_MIDPOINT" ? "Sleep time" : signal.unit, "chart-unit"));
    card.append(heading);
    const enabled = signal.registry?.enabled_in_engine !== false;
    const current = enabled ? signal.current : null;
    const patient=document.body.dataset.role==='patient';
    card.append(node("p", !enabled ? "Readings only" : current ? `${current.sensing_state === "UNOBSERVED" ? "Watch data unavailable · " : ""}${current.trust_state === "REESTABLISHING" ? "Usual being learned again" : current.trust_state === "TRUSTED" ? patient?'Your usual':'Baseline established' : "Usual still being learned"}` : "Usual still being learned", "chart-status"));
    if (signal.registry?.evidence_tier === "E3_RESEARCH") card.append(node("p", "Newer measure", "fine"));
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
    chart.append(svgNode("title", {}, signal.label), svgNode("desc", {}, "Recorded values and personal references. Exact records and sources below."));
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
    const contexts=new Map(lastEvidence.signals.flatMap(channel=>channel.contexts).map(context=>[context.event_id,context]));
    for (const context of contexts.values()) {
      const a = Math.max(start,day(context.start)), b = Math.min(end,context.end ? day(context.end) : end);
      if (a > b) continue;
      const linked=(context.affected_signals||[]).includes(signal.key.signal);
      const band = linked ? svgNode("rect",{x:x(a),y:25,width:Math.max(2,x(b)-x(a)),height:140,class:context.category === "BENIGN_CONTEXT" ? "context-band" : "risk-context-band",'data-context-linked':'true','data-context-id':context.event_id})
        : svgNode('line',{x1:x(a),x2:x(a),y1:25,y2:165,class:'context-timing-marker','data-context-linked':'false','data-context-id':context.event_id});
      band.append(svgNode("title",{},`${context.explanation || "Reported context"}; ${linked?'linked to this measure':'timing only; not linked to this measure'}`));
      chart.append(band);
    }
    for(const finding of storyFor(signal)) {
      const a=Math.max(start,day(finding.since)),b=Math.min(end,day(finding.until));if(a>b)continue;
      const link=svgNode('a',{href:`#${finding.target_id}`,'aria-label':`Finding ${finding.number}: return to sourced assessment`});
      link.append(svgNode('rect',{x:x(a),y:25,width:Math.max(3,x(b)-x(a)),height:140,class:'story-finding-band','data-finding-number':finding.number,'data-since':finding.since,'data-until':finding.until.slice(0,10)}),svgNode('circle',{cx:x(a),cy:17,r:10,class:'story-finding-marker'}),svgNode('text',{x:x(a),y:21,'text-anchor':'middle',class:'story-finding-number'},String(finding.number)));
      link.addEventListener('click',event=>{const target=document.getElementById(finding.target_id);if(target){event.preventDefault();target.scrollIntoView({block:'center',behavior:'auto'});target.focus({preventScroll:true});}});chart.append(link);
      if(finding.callout){const callout=node('a',`${finding.number} · ${finding.callout}`,'chart-callout');callout.href=`#${finding.target_id}`;callout.addEventListener('click',event=>{const target=document.getElementById(finding.target_id);if(target){event.preventDefault();target.scrollIntoView({block:'center',behavior:'auto'});target.focus({preventScroll:true});}});card.append(callout);}
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
      point.append(svgNode("title",{},`${shortDate(day(row.day))}: ${patient?valueLabel(row.value,signal):row.value} ${signal.unit} · data coverage ${row.coverage}, measurement quality ${row.data_quality}`)); chart.append(point);
    }
    if (!raw.length) chart.append(svgNode("text",{x:(width+42)/2,y:98,"text-anchor":"middle",class:"chart-empty"},"No observed values in these dates"));
    card.append(chart,drawCheckins(start,end,width));
    if (current) {
      const availability = current.rolling.coverage_ratio;
      card.append(node("p",`Data for ${availability == null ? 'an unknown number of' : Math.round(availability*14)} of 14 days · ${current.rolling.sample_count} readings.`,"fine"));
      if (current.trust_state === "REESTABLISHING") card.append(node("p","Usual being learned again; review still needed.","fine"));
      // Honest about the actual state; never promises automatic recovery.
      if (patient && (current.sensing_state === "UNOBSERVED" || current.trust_state === "REESTABLISHING"))
        card.append(node("p",`AURA doesn't currently have a usable reference for your ${signal.label.toLowerCase()}.`,"relearning-line"));
    }
    const sources = node("section",null,"chart-sources"); sources.append(node("h3",`${signal.label} — dates, sources & exact values`));
    sources.append(node("p","From: your measurements. Missing days are left blank.","fine"));
    const internal=node('p');internal.textContent=`Source: ${signal.key.source} · ${signal.key.metric||''}`;sources.append(window.auraTechnical(internal));
    if (signal.key.signal === "SLEEP_MIDPOINT") {const note=node("p","Sleep clock uses minutes from the source-local sleep-start midnight; +1d means the following day. No conversion to the viewer's timezone or circular re-analysis is performed.","fine");sources.append(patient?window.auraTechnical(note):note);}
    const anchors = new Map();
    for (const row of signal.history) if (row.anchor) anchors.set(row.anchor.version,{...row.anchor,event_id:row.event_id});
    for (const anchor of anchors.values()) {sources.append(node("p",`${patient?'Your usual':'Baseline'}: ${patient?valueLabel(anchor.center,signal):anchor.center} ${signal.unit} · ${shortDate(day(anchor.reference_start))}–${shortDate(day(anchor.reference_end))}.`,"fine"));const raw=node('p');raw.textContent=JSON.stringify(anchor);sources.append(window.auraTechnical(raw));}
    const tableWrap = node("div",null,"table-scroll"), table = node("table");
    const caption = node("caption","Recorded observations in selected dates");
    const head = node("tr"); for (const label of ["Date","Value","From"]) { const th=node("th",label); th.scope="col"; head.append(th); }
    const thead=node("thead"); thead.append(head); table.append(caption,thead);
    const tbody=node("tbody");
    for (const row of raw) { const tr=node("tr");tr.dataset.eventId=row.event_id; tr.append(node("td",shortDate(day(row.day))),node("td",`${patient?valueLabel(row.value,signal):row.value} ${signal.unit}`),node("td","Measurement")); tbody.append(tr); }
    table.append(tbody); tableWrap.append(table); sources.append(tableWrap);
    const rawRecords=node('pre');rawRecords.textContent=JSON.stringify(raw,null,2);sources.append(window.auraTechnical(rawRecords));
    document.getElementById('chart-exact-sources')?.append(sources);
    return card;
  }

  window.renderAuraEvidence = evidence => {
    if (!evidence) return;
    lastEvidence=evidence;
    // Home recap visibility and text belong to the arrival presentation service.
    // Patient charts exist only in the explicitly opened full-data workspace.
    const byId = id => document.getElementById(id);
    byId("workspace-patient").textContent = `Demo patient · ${evidence.patient.age}`;
    const overview = byId("changes-overview"); overview.replaceChildren();
    // One latest descriptive finding per signal, in the server's fixed signal order.
    // This is display selection by date, not severity ranking or a new drift decision.
    const findings = evidence.signals.flatMap(signal => signal.findings.length ?
      [signal.findings.reduce((latest,row) => day(row.last_seen) > day(latest.last_seen) ? row : latest)] : []);
    for (const finding of findings.slice(0,3)) {
      const text = node("p",`${finding.drift.description.replace(/\.$/,"")} — recorded ${shortDate(day(finding.first_seen))}–${shortDate(day(finding.last_seen))}.`);
      const detail = node("div",null,"finding-source"); detail.append(node("p",finding.drift.attenuated?'Patient context is linked to this change.':'From: watch readings.',"fine"));const raw=node('p');raw.textContent=`Source: ${finding.drift.key.source} · ${finding.event_id}`;detail.append(window.auraTechnical(raw));
      const section=node("section"); section.append(text,detail); overview.append(section);
    }
    if (!findings.length) overview.append(node("p","No descriptive change is retained in these records."));
    byId("workspace-decision").textContent = evidence.current_decision === "STAY_QUIET" ? "No question pending." : evidence.current_decision === "SAFETY_REVIEW_REQUIRED" ? "Safety interaction comes first." : "A question is available in your day view.";
    const charts = byId("evidence-charts"),otherOpen=Boolean(byId('other-measurements')?.open); charts.replaceChildren();
    let timeline=byId('finding-timeline');if(!timeline){timeline=node('section',null,'finding-timeline');timeline.id='finding-timeline';charts.before(timeline);}timeline.replaceChildren();timeline.hidden=true;
    let exact=byId('chart-exact-sources');
    if(!exact){exact=node('div');exact.id='chart-exact-sources';(byId('workspace-evidence')||charts.parentElement).append(exact);}exact.replaceChildren();
    if (evidence.period.end && evidence.period.start) {
      const end = day(evidence.period.end), allStart = day(evidence.period.start);
      const start = byId("chart-range").value === "all" ? allStart : Math.max(allStart,end-55*dayMs);
      for(const bar of document.querySelectorAll('.finding-span')){
        const a=Math.max(start,day(bar.dataset.since)),b=Math.min(end,day(bar.dataset.until)),fill=bar.firstElementChild;
        fill.hidden=a>b;fill.style.marginLeft=`${Math.max(0,Math.min(100,100*(a-start)/Math.max(dayMs,end-start)))}%`;
        fill.style.width=`${Math.max(1,Math.min(100,100*(b-a)/Math.max(dayMs,end-start)))}%`;
      }
      const spans=evidence.signals.flatMap(signal=>storyFor(signal)).filter(item=>day(item.until)>=start&&day(item.since)<=end);
      if(spans.length){
        timeline.hidden=false;timeline.append(node('p','When things changed','fine'));
        const width=640,x=at=>66+(width-90)*(at-start)/Math.max(dayMs,end-start),strip=svgNode('svg',{viewBox:`0 0 ${width} ${spans.length*22+24}`,role:'img','aria-label':'Retained finding dates on the shared chart axis'});
        spans.forEach((item,index)=>{const y=index*22+8,a=Math.max(start,day(item.since)),b=Math.min(end,day(item.until));const link=svgNode('a',{href:`#${item.target_id}`,'aria-label':`Finding ${item.number}, ${shortDate(a)} to ${shortDate(b)}`});link.append(svgNode('text',{x:56,y:y+10,'text-anchor':'end',class:'finding-timeline-label'},String(item.number)),svgNode('rect',{x:66,y,width:width-90,height:10,rx:5,class:'finding-timeline-track'}),svgNode('rect',{x:x(a),y,width:Math.max(3,x(b)-x(a)),height:10,rx:5,class:'finding-timeline-span','data-finding-number':item.number}));link.addEventListener('click',event=>{const target=document.getElementById(item.target_id);if(target){event.preventDefault();target.scrollIntoView({block:'center',behavior:'auto'});target.focus({preventScroll:true});}});strip.append(link);});
        for(const at of [start,end])strip.append(svgNode('text',{x:x(at),y:spans.length*22+18,'text-anchor':at===start?'start':'end',class:'finding-timeline-label'},shortDate(at)));timeline.append(strip);
      }
      const coreOrder=['SLEEP_MIDPOINT','SLEEP_DURATION','ACTIVITY','RESTING_HEART_RATE'];
      const groups={core:[],moved:[],other:[]};
      for(const signal of evidence.signals){
        const readings=signal.observations.filter(row=>!row.deferred&&day(row.day)>=start&&day(row.day)<=end).length;
        const group=readings<3?'other':coreOrder.includes(signal.key.signal)?'core':storyFor(signal).length?'moved':'other';
        groups[group].push(signal);
      }
      groups.core.sort((a,b)=>coreOrder.indexOf(a.key.signal)-coreOrder.indexOf(b.key.signal));
      for(const signal of groups.core)charts.append(drawChart(signal,start,end));
      if(groups.moved.length){const moved=node('section',null,'chart-group');moved.id='also-moved';moved.append(node('h2','Also moved'));const grid=node('div',null,'chart-group-grid');for(const signal of groups.moved)grid.append(drawChart(signal,start,end));moved.append(grid);charts.append(moved);}
      if(groups.other.length){const other=node('details',null,'chart-group other-measurements');other.id='other-measurements';other.open=otherOpen;other.append(node('summary',`Other measurements (${groups.other.length})`));const grid=node('div',null,'chart-group-grid');for(const signal of groups.other)grid.append(drawChart(signal,start,end));other.append(grid);charts.append(other);}
    } else charts.append(node("p","No recorded history yet."));
    const strip = byId("evidence-strip"); strip.replaceChildren();
    for (const [title,rows,field] of [["Check-ins · patient reports",evidence.checkins,"state"],["Medication: patient-reported",evidence.medication,"status"]]) {
      const section=node("section"), entries=node("div",null,"categorical-strip");
      const end=evidence.period.end ? day(evidence.period.end) : 0;
      const start=byId("chart-range").value === "all" ? -Infinity : end-55*dayMs;
      const visibleRows=rows.filter(row=>day(row.at)>=start && day(row.at)<=end);
      const preview=node("div",null,"categorical-strip reports-preview");
      preview.append(node("span",`${title} · latest ${Math.min(7,visibleRows.length)} in chart dates`,"fine"));
      for (const row of visibleRows.slice(-7)) preview.append(node("span",`${shortDate(day(row.at))} · ${row[field]}${row.deferred ? " · held" : ""}`,"report-dot"));
      if(!visibleRows.length) preview.append(node("span","None recorded in chart dates", "fine"));
      for (const row of visibleRows) {
        const entry=node("span",`${shortDate(day(row.at))} · ${row[field]}${row.deferred ? " · held pending safety evaluation" : ""}`,"report-dot");
        entry.title=`${shortDate(day(row.at))} · patient-reported`;entry.dataset.eventId=row.event_id; entries.append(entry);
      }
      section.append(preview); strip.append(section);
      exact.append(node('h3',`${title} · exact records`),entries);
    }
    const safety=byId("safety-evidence"); safety.replaceChildren();
    const safetyStatus={OPEN:'active',CLOSED:'closed',RECHECK_REQUIRED:'another check pending',DROPOUT:'follow-up interrupted',NONE:'no open interaction'};
    for (const ref of evidence.safety.references) {safety.append(node('p',`${ref.at?shortDate(day(ref.at)):'Date unavailable'} · Safety interaction: ${safetyStatus[ref.state.episode_status]||'recorded'}${ref.state.degraded?' · Some safety information unavailable':''}.`,'fine'));const raw=node('pre');raw.textContent=JSON.stringify(ref,null,2);safety.append(window.auraTechnical(raw));}
    if (!evidence.safety.references.length) safety.append(node("p","No safety episode references recorded."));
    safety.append(node("p","No clinician or emergency service is automatically notified. Current policy output and separate resources stay outside this history section.","fine"));
    if(byId("workspace-safety")?.tagName==='DETAILS')byId("workspace-safety").open = Boolean(evidence.safety.state?.episode_id || evidence.safety.state?.degraded);
    const review=byId("evidence-review"); review.replaceChildren();
    const treatment=evidence.patient.treatment||{};
    review.append(node("p",`Recorded treatment context: ${treatment.medication_name || "not recorded"} · schedule ${treatment.medication_schedule || "not recorded"} · stable since ${treatment.stable_since || "not recorded"} · next review ${treatment.next_review || "not configured"}.`,"fine"));
    for(const row of evidence.questions) review.append(node("p",`${row.question} · ${shortDate(day(row.at))}`,"fine"));
    if(!evidence.questions.length)review.append(node("p","No patient-selected questions recorded.","fine"));
    for(const row of evidence.review_items)review.append(node("p",`${row.summary} · ${row.status} · not shared`,"fine"));
    if(!evidence.review_items.length)review.append(node("p","No review items prepared.","fine"));
    if(byId("workspace-review")?.tagName==='DETAILS')byId("workspace-review").open=Boolean(evidence.questions.length);
    comparison(evidence);
  };
  function selectedDates(evidence){
    if(!evidence.period.start||!evidence.period.end)return null;
    const end=day(evidence.period.end),allStart=day(evidence.period.start);
    return {start:document.getElementById('chart-range').value==='all'?allStart:Math.max(allStart,end-55*dayMs),end};
  }
  function comparison(evidence){
    let toggle=document.getElementById('record-comparison-toggle'),panel=document.getElementById('record-comparison');
    if(!toggle){
      toggle=node('button','Compare raw record with AURA','secondary');toggle.id='record-comparison-toggle';toggle.type='button';toggle.setAttribute('aria-expanded','false');toggle.setAttribute('aria-controls','record-comparison');
      document.getElementById('chart-range').closest('.workspace-heading').after(toggle);
      panel=node('section',null,'record-comparison');panel.id='record-comparison';panel.hidden=true;toggle.after(panel);
      toggle.addEventListener('click',()=>{comparisonOpen=!comparisonOpen;toggle.setAttribute('aria-expanded',String(comparisonOpen));comparison(lastEvidence);});
    }
    panel.hidden=!comparisonOpen;if(!comparisonOpen)return;
    const dates=selectedDates(evidence);panel.replaceChildren();if(!dates)return;
    panel.dataset.start=new Date(dates.start).toISOString().slice(0,10);panel.dataset.end=new Date(dates.end).toISOString().slice(0,10);
    panel.append(node('h2','Same record, two presentations'),node('p',`${panel.dataset.start}–${panel.dataset.end}. Recorded measurements and sourced observations.`,'fine'));
    const grid=node('div',null,'comparison-columns'),raw=node('section'),summary=node('section');raw.append(node('h3','Raw measurements'));
    const rows=evidence.signals.flatMap(signal=>signal.observations.filter(row=>day(row.day)>=dates.start&&day(row.day)<=dates.end).map(row=>({date:row.day,signal:signal.label,source:signal.key.source,metric:signal.key.metric||'',value:row.value,unit:signal.unit,coverage:row.coverage,quality:row.data_quality,deferred:row.deferred,event:row.event_id})))
      .sort((a,b)=>a.date.localeCompare(b.date)||a.signal.localeCompare(b.signal)||a.source.localeCompare(b.source)||a.metric.localeCompare(b.metric)||a.event.localeCompare(b.event));
    const table=node('table'),thead=node('thead'),head=node('tr');for(const label of ['Date','Signal / source','Value','Coverage']){const th=node('th',label);th.scope='col';head.append(th);}thead.append(head);table.append(node('caption','Actual records only; absent days are not filled or interpolated'),thead);
    const tbody=node('tbody');for(const row of rows){const tr=node('tr');tr.append(node('td',row.date),node('td',row.signal),node('td',`${document.body.dataset.role==='patient'?Math.round(row.value*10)/10:row.value} ${row.unit}${row.deferred?' · held':''}`),node('td',String(row.coverage)));tbody.append(tr);}table.append(tbody);
    const internal=node('pre');internal.textContent=JSON.stringify(rows,null,2);raw.append(window.auraTechnical(internal));
    const wrap=node('div',null,'table-scroll');wrap.append(table);raw.append(wrap,node('p',`${rows.length} committed measurement rows. Missing days have no row.`,'fine'));
    const download=node('button','Export these raw dates (CSV)','secondary');download.type='button';download.addEventListener('click',()=>{
      const fields=['date','signal','source','metric','value','unit','coverage','quality','deferred','event'];
      const quote=value=>'"'+String(value??'').replaceAll('"','""')+'"';
      const content=[fields.join(','),...rows.map(row=>fields.map(field=>quote(row[field])).join(','))].join('\r\n');
      const url=URL.createObjectURL(new Blob([content],{type:'text/csv;charset=utf-8'}));const link=node('a');link.href=url;link.download=`aura-synthetic-record-${panel.dataset.start}-${panel.dataset.end}.csv`;link.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
    });raw.append(download);summary.append(node('h3','AURA — sourced observations in these dates'));
    // Comparison selection is by committed dates, not clinical ranking or new analysis.
    for(const signal of evidence.signals)for(const finding of signal.findings){
      if(day(finding.last_seen)<dates.start||day(finding.first_seen)>dates.end)continue;
      summary.append(node('p',`${finding.drift.description} ${shortDate(day(finding.first_seen))}–${shortDate(day(finding.last_seen))}. From: measurements.`));
    }
    if(summary.children.length===1)summary.append(node('p','No retained descriptive finding in these dates.'));
    if(comparisonAssessment?.draft?.claims?.length){
      const sourced=node('section',null,'comparison-assessment');sourced.append(node('h4','Current checked assessment — matching dates'));
      const sources=comparisonAssessment.sources||[];
      for(const claim of comparisonAssessment.draft.claims){
        const facts=(claim.fact_ids||[]).map(id=>sources.find(fact=>fact.fact_id===id));
        // An undated or out-of-window claim is never passed off as this window's synthesis.
        const matches=facts.length>0&&facts.every(fact=>{
          if(!fact)return false;
          if(fact.finding?.since&&fact.at)return day(fact.finding.since)>=dates.start&&day(fact.at)<=dates.end;
          return fact.at&&day(fact.at)>=dates.start&&day(fact.at)<=dates.end;
        });
        if(!matches)continue;
        const line=node('p',claim.text);line.append(node('span',` From: ${facts.map(fact=>fact.patient?.source_label||'measurements').join(', ')}.`,'fine'));const internal=node('p');internal.textContent=`Sources: ${facts.map(fact=>fact.source_ref).join(', ')}`;line.append(window.auraTechnical(internal));sourced.append(line);
      }
      if(sourced.children.length===1)sourced.append(node('p','No checked assessment claim is wholly dated within this selected range. Retained observations above still describe these dates.','fine'));
      summary.append(sourced);
    }
    summary.append(node('p','Committed findings above overlap these chart dates. Checked assessment claims appear only when all cited facts fall within these dates; no new model call or analysis is made.','fine'));
    grid.append(raw,summary);panel.append(grid);
  }
  window.linkAuraStoryFindings=(items,sources=[])=>{
    storyItems=Array.isArray(items)?items:[];storySources=Array.isArray(sources)?sources:[];
    if(lastEvidence)window.renderAuraEvidence(lastEvidence);
    for(const item of storyItems){const target=document.getElementById(item.target_id||`story-finding-${item.number}`);if(!target)continue;
      target.querySelector('.story-chart-link')?.remove();const match=lastEvidence?.signals.find(signal=>storyFor(signal).some(row=>row.number===item.number));if(!match)continue;
      const link=node('a','See on chart','story-chart-link');link.href=`#${chartId(match.key)}`;link.addEventListener('click',event=>{const chart=document.getElementById(chartId(match.key));if(chart){event.preventDefault();revealChart(chart);}});target.append(link);
    }
  };
  window.setAuraComparisonAssessment=result=>{comparisonAssessment=result||null;if(lastEvidence)comparison(lastEvidence);};
  window.clearAuraStory=()=>{comparisonAssessment=null;window.linkAuraStoryFindings([],[]);};
  window.addEventListener("resize",()=>{
    clearTimeout(resizeTimer);
    resizeTimer=setTimeout(()=>{if(lastEvidence)window.renderAuraEvidence(lastEvidence);},100);
  });
})();
