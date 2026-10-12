/* Read-only presentation. Existing server guards own generation permission. */
"use strict";
(() => {
  const node=(tag,text,cls)=>{const e=document.createElement(tag);if(text!=null)e.textContent=window.auraPlain(text);if(cls)e.className=cls;return e;};
  // Readable clinician values: clock times for sleep, rounded numbers elsewhere.
  const clockOf=value=>{const m=((Math.round(value)%1440)+1440)%1440;return `${String(Math.floor(m/60)).padStart(2,'0')}:${String(m%60).padStart(2,'0')}`;};
  const hoursMinutes=minutes=>{const m=Math.round(Math.abs(minutes)),h=Math.floor(m/60),r=m%60;return h?`${h} h${r?` ${r} min`:''}`:`${r} min`;};
  const plainNumber=value=>new Intl.NumberFormat('en-GB',{maximumFractionDigits:Math.abs(value)<1?2:Math.abs(value)<100?1:0}).format(value);
  function formatValue(signalName,unit,value,{difference=false}={}){
    if(typeof value!=='number'||!Number.isFinite(value))return 'unavailable';
    if(signalName==='SLEEP_MIDPOINT'||String(unit).startsWith('minutes since'))return difference?`${hoursMinutes(value)} ${value>=0?'later':'earlier'}`:clockOf(value);
    const sign=difference&&value>0?'+':'';
    if(signalName==='ACTIVITY'&&['steps','step'].includes(unit))return `${sign}${new Intl.NumberFormat('en-GB',{maximumFractionDigits:0}).format(Math.round(value))} steps a day`;
    return `${sign}${plainNumber(value)} ${signalName==='SKIN_TEMPERATURE_DEVIATION'?'°C':unit}`;
  }
  window.auraFormatValue=formatValue;
  let staleRetries=0;
  const technicalText=text=>{const p=node('p',null,'fine');p.textContent=text;return p;};
  const friendly=fact=>fact.patient?fact.patient.text||'A measurement or note was included.':window.auraPlain(fact.text);
  const sourceLine=fact=>`${fact.patient?.source_label|| (fact.checkin_summary?'Your check-ins':'Your measurements')}${fact.patient?.date_label?' · '+fact.patient.date_label:fact.at?' · '+date(fact.at):''}`;
  function factSources(facts,patient=false){
    const section=node('section',null,'friendly-sources');
    for(const fact of facts.filter(Boolean))section.append(node('p',patient?friendly(fact):fact.text,'fine'),node('p',sourceLine(fact),'fine'));
    section.append(window.auraTechnical(...facts.filter(Boolean).map(fact=>technicalText(`${fact.fact_id} · ${fact.raw_text||fact.text} · Source: ${fact.source_ref} · ${JSON.stringify(fact)}`))));
    return section;
  }
  let identity='',requestEpoch=0; const pending=new Map(), completed=new Map(), priorLines=new Map(),rendered=new WeakMap();
  const prep=node('section',null,'card agent-card');prep.append(node('h2','Your visit note'),node('p','Choose what to bring. Not sent.','fine'));
  const button=node('button','Help prepare my note');button.dataset.agentRole='visit_prep';
  const output=node('div');output.id='agent-visit_prep';output.setAttribute('aria-live','polite');prep.append(button,output);document.getElementById('appointment-preview').before(prep);
  const icons={SLEEP_MIDPOINT:'☾',SLEEP_DURATION:'☾',ACTIVITY:'↟',RESTING_HEART_RATE:'♡',HRV:'↔',HEART_RATE_VARIABILITY:'↔',RESPIRATORY_RATE:'≋',SKIN_TEMPERATURE_DEVIATION:'°'};
  const titles={SLEEP_MIDPOINT:'Sleep timing',SLEEP_DURATION:'Sleep duration',ACTIVITY:'Activity',RESTING_HEART_RATE:'Resting heart rate',SKIN_TEMPERATURE_DEVIATION:'Skin temperature'};
  const patientTitles={SLEEP_MIDPOINT:'Sleep timing',SLEEP_DURATION:'Time asleep',ACTIVITY:'Activity',RESTING_HEART_RATE:'Resting heart rate',HRV:'Heart rate variation',HEART_RATE_VARIABILITY:'Heart rate variation',RESPIRATORY_RATE:'Breathing rate',SKIN_TEMPERATURE_DEVIATION:'Skin temperature'};
  const date=at=>new Intl.DateTimeFormat('en-GB',{day:'numeric',month:'short',timeZone:'UTC'}).format(new Date(at.slice(0,10)+'T00:00:00Z'));
  const everydayDate=at=>{const d=new Date(at.slice(0,10)+'T00:00:00Z');return `${d.getUTCDate()<=10?'early':d.getUTCDate()<=20?'mid':'late'} ${new Intl.DateTimeFormat('en-GB',{month:'long',timeZone:'UTC'}).format(d)}`;};
  // Resolve only an exact committed finding; never derive a drift or a magnitude from prose.
  function presentation(finding,sources){
    const fact=sources.find(f=>f.fact_id===finding.fact_id),record=window.auraAgentContext().record;
    if(!fact?.finding||!record)return null;
    const matches=record.signals.flatMap(signal=>signal.findings.map(row=>({signal,row}))).filter(({signal,row})=>
      signal.key.signal===finding.signal&&row.event_id===fact.source_ref&&row.first_seen.slice(0,10)===finding.since&&row.last_seen.slice(0,10)===fact.at);
    if(matches.length!==1)return null;
    const {signal,row}=matches[0],delta=row.drift.kind==='TRANSIENT_DEVIATION'?row.drift.current_vs_rolling:row.drift.rolling_vs_anchor;
    const snapshot=signal.history?.find(snapshot=>snapshot.event_id===fact.source_ref);
    const direction={LATER:'later',EARLIER:'earlier',HIGHER:'higher',LOWER:'lower'}[finding.direction];
    if(!direction)return null;
    const amount=Number.isFinite(delta)?Math.abs(delta):null;
    let magnitude=`${direction} than ${row.drift.kind==='TRANSIENT_DEVIATION'?'your recent pattern':'your usual'}`;
    if(amount!==null){
      const formatted=signal.unit.startsWith('minutes')?(amount>=60?`${Math.round(amount/60*2)/2} h`:`${Math.round(amount)} min`):
        signal.key.signal==='ACTIVITY'&&['steps','step'].includes(signal.unit)?`${new Intl.NumberFormat('en-GB').format(Math.round(amount/100)*100)} steps a day`:
        `${new Intl.NumberFormat('en-GB',{maximumFractionDigits:1}).format(amount)} ${signal.key.signal==='SKIN_TEMPERATURE_DEVIATION'?'°C':signal.unit}`;
      // A small nonzero value must not be displayed as an apparent zero change.
      if(amount>0&&!/^0(?: |\.0 )/.test(formatted))magnitude=`about ${formatted} ${signal.key.signal==='ACTIVITY'?(delta<0?'fewer':'more'):direction}`;
    }
    const transient=row.drift.kind==='TRANSIENT_DEVIATION',label=titles[finding.signal]||signal.label;
    const wording=transient?`${label}: recent change`:(finding.signal==='SLEEP_MIDPOINT'?`Sleeping ${direction} than usual`:`${label} ${direction} than usual`);
    return {label,icon:icons[finding.signal]||'◌',magnitude,wording,delta,transient,channel:JSON.stringify(signal.key),lastSeen:row.last_seen,unit:signal.unit,since:finding.since,until:fact.at,
      line:`${transient?'Recent change':`${direction[0].toUpperCase()+direction.slice(1)} than usual`} · ${date(finding.since)}–${date(fact.at)}`,
      source:fact.source_ref,method:row.drift.kind==='TRANSIENT_DEVIATION'?'Current reading compared with recent average':'Recent average compared with baseline',
      exact:`Difference: ${formatValue(finding.signal,signal.unit,delta,{difference:true})}.${snapshot?` Recent average: ${formatValue(finding.signal,signal.unit,snapshot.rolling.mean)}. Baseline: ${snapshot.anchor?formatValue(finding.signal,signal.unit,snapshot.anchor.center):'still being learned'}. Median: ${formatValue(finding.signal,signal.unit,snapshot.rolling.median)}.`:''}`,
      recordStart:record.period.start?.slice(0,10),recordEnd:record.period.end?.slice(0,10)};
  }
  function findingCard(claim,result,role,number){
    const finding=claim.findings?.[0],display=finding&&presentation(finding,result.sources);
    if(!display)return null;
    const patient=role==='patient_insight',card=node('section',null,`agent-claim finding-card ${patient?'patient-finding':'clinician-finding'}`);
    card.dataset.signal=finding.signal;card.dataset.source=display.source;card.dataset.channel=display.channel;
    const header=node('div',null,'finding-card-heading'),icon=node('span',display.icon,'signal-icon');icon.setAttribute('aria-hidden','true');
    const patientLabel=patientTitles[finding.signal]||display.label;
    const patientDirection={LATER:'later',EARLIER:'earlier',HIGHER:'higher',LOWER:'lower'}[finding.direction];
    const patientWording=finding.signal==='SLEEP_MIDPOINT'?`Sleeping ${patientDirection} than ${display.transient?'recently':'usual'}`:`${patientLabel} ${patientDirection} than ${display.transient?'recently':'usual'}`;
    header.append(icon,node('h4',patient?patientWording:display.label));
    if(!patient){card.id=`story-finding-${number}`;card.tabIndex=-1;header.append(node('span',String(number),'finding-number'));}
    const show=node('button',patient?'Why? / Sources':'Why?','text-button finding-why');show.type='button';show.setAttribute('aria-expanded','false');header.append(show);card.append(header);
    if(patient){card.append(node('p',`${display.transient?'Recorded':'Since'} ${everydayDate(display.since)}`,'finding-date'),node('span',display.transient?'Recent change':'shifted','badge finding-state'));}
    else{
      if(display.transient)card.append(node('span','Recent change','badge finding-state'));
      card.append(node('p',`${['LOWER','EARLIER'].includes(finding.direction)?'↓':'↑'} ${display.magnitude}`,'finding-magnitude'));
      const span=node('div',null,'finding-span');span.dataset.since=display.since;span.dataset.until=display.until;span.setAttribute('aria-label',`Recorded span ${date(display.since)} to ${date(display.until)}`);
      span.append(node('span'));card.append(span,node('p',display.line,'finding-one-liner'));
      card.append(node('p',display.exact,'finding-exact'));
    }
    const detail=node('section',null,'claim-sources finding-detail');detail.hidden=true;detail.id=`finding-detail-${role}-${number}`;show.setAttribute('aria-controls',detail.id);
    detail.append(node('p',patient?display.wording:display.method,'finding-method'),factSources(claim.fact_ids.map(id=>result.sources.find(f=>f.fact_id===id)),patient));
    if(claim.earlier?.length){detail.append(node('h5','Earlier dates'),factSources(claim.earlier,patient));}
    show.addEventListener('click',()=>{detail.hidden=!detail.hidden;show.setAttribute('aria-expanded',String(!detail.hidden));});card.append(detail);
    if(patient)card.addEventListener('click',event=>{if(!event.target.closest('button,a')&&!detail.contains(event.target))show.click();});
    return {card,link:{...finding,number,target_id:card.id,callout:display.line}};
  }
  const displayText=text=>text.replace(/\b\d{4}-\d{2}-\d{2}\b/g,at=>everydayDate(at))
    .replace(/\b\d+\.\d+\b/g,value=>new Intl.NumberFormat('en-GB',{maximumFractionDigits:1}).format(Number(value)));
  function render(result,area,role){
    const ctx=window.auraAgentContext(),paused=result.status==='BLOCKED'||result.status==='STALE';
    const recordKey=result.state_fingerprint?JSON.stringify([ctx.patientId,ctx.revision,role,result.state_fingerprint]):null;
    const signature=JSON.stringify(result),last=rendered.get(area);
    // The caller has just checked a fresh server guard. Repeated unchanged
    // responses need not replace the DOM under an actively inspected source panel.
    const sameRecord=!paused&&!ctx.offline&&recordKey&&last?.recordKey===recordKey;
    if(sameRecord&&last.signature===signature&&area.childElementCount)return;
    const disclosureSelectors=['.patient-summary-details','.patient-summary-sources','.patient-retained-sources'];
    const openDisclosures=sameRecord?disclosureSelectors.filter(selector=>area.querySelector(selector)?.open):[];
    const findingKey=card=>JSON.stringify([card.dataset.channel,card.dataset.source,card.dataset.signal]);
    const openFindings=sameRecord?new Set([...area.querySelectorAll('.clinician-finding')]
      .filter(card=>card.querySelector('.finding-detail')?.hidden===false).map(findingKey)):new Set();
    const previous=priorLines.get(role)||new Set(), now=new Set();area.replaceChildren();
    if(paused||ctx.offline)rendered.delete(area);else rendered.set(area,{recordKey,signature});
    // A stale result only means the record changed while it was being written: refresh quietly (a few times), no safety message.
    if(result.status==='STALE'&&staleRetries<3&&!ctx.offline){staleRetries++;area.append(node('p','Updating the summary…','fine'));setTimeout(()=>window.refreshAuraAssessment?.(),1500);return;}
    if(result.status!=='STALE')staleRetries=0;
    const bounded=['clinician_brief','patient_insight'].includes(role),visibleAI=result.generation_used&&(!bounded||Boolean(result.draft.headline))&&(role!=='patient_insight'||Boolean(result.headline_fact_ids?.length));
    const label=paused?'Assessment paused':visibleAI?'AI-written · sources checked':'Summary from the record';
    const chip=node('span',label,'agent-disclosure badge');chip.title=result.disclosure;if(role!=='patient_insight')area.append(chip);
    if(paused){document.getElementById('assessment-complete')?.replaceChildren();window.clearAuraStory?.();document.getElementById('agent-visit_prep')?.replaceChildren();area.append(node('p','Safety interaction or record evaluation comes first. See the separate safety panel.'));return;}
    if(result.draft.headline&&role!=='patient_insight')area.append(node('h3',result.draft.headline.split(/\s+/).slice(0,20).join(' ')));
    const summary=result.record_presentation;
    if(role==='clinician_brief'&&summary?.synthesis){
      const line=node('section',null,'assessment-synthesis');line.append(node('p',summary.synthesis.text));
      const detail=node('details');detail.append(node('summary','Sources'));
      detail.append(factSources(summary.synthesis.fact_ids.map(id=>result.sources.find(f=>f.fact_id===id))));
      line.append(detail);area.append(line);
    }
    const allClaims=result.draft.claims||[],latest=new Map();
    if(bounded)for(const fact of result.sources.filter(f=>f.finding)){
      const finding={fact_id:fact.fact_id,...fact.finding},display=presentation(finding,result.sources);if(!display)continue;
      const candidate={text:fact.text,fact_ids:[fact.fact_id],findings:[finding],display,earlier:[]},prior=latest.get(display.channel);
      if(!prior)latest.set(display.channel,candidate);
      else if(display.lastSeen>prior.display.lastSeen||(display.lastSeen===prior.display.lastSeen&&display.since>prior.display.since)){candidate.earlier=[...prior.earlier,result.sources.find(f=>f.fact_id===prior.fact_ids[0])];latest.set(display.channel,candidate);}
      else prior.earlier.push(fact);
    }
    const displayed=bounded?[...latest.values()].sort((a,b)=>role==='patient_insight'?
      b.display.since.localeCompare(a.display.since)||b.display.lastSeen.localeCompare(a.display.lastSeen):
      b.display.lastSeen.localeCompare(a.display.lastSeen)):allClaims;
    let recapSources=[];
    if(role==='patient_insight'){
      const heading=document.getElementById('home-heading');if(heading)heading.textContent='Your day, with AURA';
      if(visibleAI&&result.draft.headline){
        area.append(node('p',result.draft.headline,'patient-recap'));
        recapSources=(result.headline_fact_ids||[]).map(id=>result.sources.find(f=>f.fact_id===id)).filter(Boolean);
      }
      else if(result.draft.headline&&(!result.generation_used||result.fallback_headline_fact_ids?.length)){area.append(node('p',result.draft.headline,'patient-recap'));const ids=result.headline_fact_ids?.length?result.headline_fact_ids:result.fallback_headline_fact_ids?.length?result.fallback_headline_fact_ids:[...new Set(allClaims.flatMap(claim=>claim.fact_ids||[]))];recapSources=ids.map(id=>result.sources.find(f=>f.fact_id===id)).filter(Boolean);}
      else if(displayed.length){
        const everyday=displayed.filter(c=>['SLEEP_MIDPOINT','ACTIVITY','SLEEP_DURATION'].includes(c.findings[0].signal));
        const selected=(everyday.length?everyday:displayed).slice(0,1);
        recapSources=selected.flatMap(c=>c.fact_ids.map(id=>result.sources.find(f=>f.fact_id===id))).filter(Boolean);
        const fact=recapSources[0];area.append(node('p',fact?.patient?.recap_text||fact?.patient?.text||'Your recent entries are available below.','patient-recap'));
      }else if(summary?.checkins){
        area.append(node('p',`You've marked recent days as ${summary.checkins.checkin_summary.state} in your check-ins.`,'patient-recap'));
        recapSources=[summary.checkins];
      }
    }
    const patientDetails=role==='patient_insight'?node('details',null,'patient-summary-details'):null;
    if(patientDetails){patientDetails.append(node('summary','See what changed'));area.append(patientDetails);}
    const claimArea=patientDetails||area;
    const linkage=[],grid=node('div',null,'finding-grid');let number=0;claimArea.append(grid);
    let extraGrid=null;
    const cap=role==='patient_insight'?Infinity:6;
    if(bounded&&displayed.length>cap){const more=node('details',null,'more-changes');more.append(node('summary',role==='patient_insight'?`See all (${displayed.length} changes)`:`More changes (${displayed.length-cap})`));extraGrid=node('div',null,'finding-grid');more.append(extraGrid);area.append(more);}
    for(const claim of displayed){
      const key=JSON.stringify([claim.text,claim.findings,claim.fact_ids.map(id=>result.sources.find(f=>f.fact_id===id)?.source_ref)]);now.add(key);
      const shaped=['clinician_brief','patient_insight'].includes(role)&&findingCard(claim,result,role,number+1);
      if(shaped){number++;if(previous.size&&!previous.has(key))shaped.card.classList.add('assessment-changed');(extraGrid&&number>cap?extraGrid:grid).append(shaped.card);if(role==='clinician_brief')linkage.push(shaped.link);continue;}
      const line=node('section',null,'agent-claim');if(!claim.findings?.length){line.classList.add('also-recorded','fine');line.append(node('span','Also recorded','fine'));}if(previous.size&&!previous.has(key))line.classList.add('assessment-changed');
      if(role==='clinician_brief'&&claim.findings?.length){number++;line.id=`story-finding-${number}`;line.tabIndex=-1;line.append(node('span',String(number),'finding-number'));for(const finding of claim.findings)linkage.push({...finding,number,target_id:line.id});}
      line.append(node('p',role==='clinician_brief'||claim.findings?.length?claim.text:displayText(claim.text)));
      if(role==='clinician_brief')for(const finding of claim.findings||[]){
        const origin=result.sources.find(f=>f.fact_id===finding.fact_id);
        const metric=result.sources.find(f=>f.source_ref===origin?.source_ref&&f.signal===finding.signal&&!f.finding&&/deviation/.test(f.text));
        if(metric&&!claim.text.includes(metric.text)){
          const deviation=metric.text.match(/rolling versus own reference deviation ([^;]+);?/);
          line.append(node('p',`${deviation?`Compared with your usual: ${deviation[1]}`:metric.text} · Source extraction`,'fine'));
        }
      }
      const sources=node('div',null,'claim-sources');sources.hidden=true;
      sources.append(factSources(claim.fact_ids.map(id=>result.sources.find(f=>f.fact_id===id)),role!=='clinician_brief'));
      const show=node('button','Sources','text-button');show.setAttribute('aria-expanded','false');show.addEventListener('click',()=>{sources.hidden=!sources.hidden;show.setAttribute('aria-expanded',String(!sources.hidden));});line.append(show,sources);
      if(role==='visit_prep'){const remove=node('button','Remove from this preview','text-button');remove.addEventListener('click',()=>line.remove());line.append(remove);}claimArea.append(line);
    }
    if(role==='patient_insight'&&allClaims.length&&summary?.checkins){
      const fact=summary.checkins,r=fact.checkin_summary,card=node('section',null,'checkin-summary-card patient-checkins');
      card.append(node('h4',`Recent check-ins: ${r.state}`),node('p',`${r.count} of the last ${r.window_days} days · patient-reported`));
      const detail=node('details');detail.append(node('summary','Why? / Sources'),factSources([fact],true));card.append(detail);grid.append(card);
    }
    if(role==='clinician_brief'&&summary?.checkins){
      const fact=summary.checkins,r=fact.checkin_summary,card=node('section',null,'checkin-summary-card clinician-checkins');
      card.append(node('h4','Check-ins'),node('p','Patient-reported','fine'),
        node('p',`${r.state} on ${r.count} of the last ${r.window_days} days`),
        node('p',`${r.run_days} consecutive recorded days, since ${date(r.run_start)}`,'fine'));
      const detail=node('details');detail.append(node('summary','Why? / Sources'),factSources([fact]));card.append(detail);grid.append(card);
    }
    priorLines.set(role,now);
    if(role==='clinician_brief'){
      const readings=result.sources.filter(f=>f.reading);
      if(readings.length){const group=node('section',null,'recent-readings');group.append(node('h4','Recent readings'));for(const fact of readings){
        const r=fact.reading;
        const row=node('section',null,'reading-item');row.dataset.signal=fact.signal;
        row.append(node('h5',`${r.label}: ${r.latest} ${r.unit} · ${r.count} readings · ${date(r.start)}–${date(r.end)}`));
        row.append(node('p',`${r.median==null?'':`Median: ${r.median} ${r.unit}. `}Range: ${r.minimum}–${r.maximum} ${r.unit}.`),factSources([fact]));group.append(row);
      }area.append(group);}
      for(const [title,kind,empty] of [['Context recorded','get_context','No associated context in these facts.'],['Data gaps','get_gaps','No gaps in the retrieved facts.']]){
        const facts=result.sources.filter(f=>kind==='get_gaps'?/SENSING_GAP|SENSING_RETURN/.test(f.raw_text||f.text):/context recorded|patient-reported context/.test(f.raw_text||f.text));
        if(!facts.length)continue;
        const group=node('section',null,'assessment-subsection');group.append(node('h4',title));
        for(const fact of facts.slice(0,2))group.append(node('p',fact.text,'fine'));area.append(group);
      }
      const questions=node('section');questions.append(node('h4','Worth asking'));
      if(result.draft.question_ids?.length)area.append(questions);
      const complete=document.getElementById('assessment-complete');if(complete){complete.replaceChildren(node('h3','Complete sourced assessment'));for(const c of allClaims)complete.append(node('p',c.text));complete.append(factSources(result.sources));}
      window.linkAuraStoryFindings?.(linkage,result.sources);
      window.setAuraComparisonAssessment?.(result);
    }
    // Worth asking belongs to clinician preparation, not a new patient prompt.
    // Patient interaction remains owned by the separate communication result.
    for(const id of role==='patient_insight'?[]:(result.draft.question_ids||[])){const text=result.question_options[id];if(!text)continue;const copy=node('button',text,'agent-question question-copy');copy.type='button';copy.title='Copy this approved question';copy.addEventListener('click',async()=>{try{await navigator.clipboard.writeText(text);copy.setAttribute('aria-label',`${text} — copied`);}catch{const input=document.getElementById('agent-question-text');input.value=text;input.focus();}});area.append(copy);}
    if(!allClaims.length&&!result.draft.question_ids?.length&&!(role==='patient_insight'&&summary?.checkins))area.append(node('p','Nothing additional to highlight from these records.'));
    const trace=node('section',null,'agent-trace');trace.hidden=true;
    trace.append(node('p',`Run ${result.run_id} · ${result.model_id||'not called'} · ${result.reason} · ${result.elapsed_ms||0} ms`,'fine'));
    for(const entry of result.trace||[])trace.append(node('p',entry.tool?`${entry.tool}: ${(entry.fact_ids||[]).length} linked facts`:entry.action,'fine'));
    trace.hidden=false;
    if(role!=='patient_insight')area.append(window.auraTechnical(trace));
    else{
      const why=node('details',null,'patient-summary-sources');why.append(node('summary','Why this summary?'),chip,node('h4','What we looked at'),node('p',[...new Set(recapSources.map(fact=>fact.patient?.source_label||'Your measurements'))].join(' and ')||'Your recent entries.'));
      why.append(node('h4','What we saw'));
      for(const fact of recapSources){const line=node('p',friendly(fact),'fine patient-recap-source');line.dataset.factId=fact.fact_id;why.append(line);}
      why.append(node('h4','Where it comes from'));
      for(const fact of recapSources)why.append(node('p',sourceLine(fact),'fine'));
      why.append(window.auraTechnical(...recapSources.map(fact=>technicalText(`${fact.fact_id} · ${fact.raw_text||fact.text} · Source: ${fact.source_ref} · ${JSON.stringify(fact)}`))));
      const retained=node('details',null,'patient-retained-sources');retained.append(node('summary','All recorded details'));
      retained.append(factSources(result.sources,true),window.auraTechnical(trace));why.append(retained);area.append(why);
    }
    // Preserve only the open explanation state for an identical evidence identity.
    // Its contents come from this newly guarded result; technical folds stay closed.
    for(const card of area.querySelectorAll('.clinician-finding'))if(openFindings.has(findingKey(card))){card.querySelector('.finding-detail').hidden=false;card.querySelector('.finding-why').setAttribute('aria-expanded','true');}
    if(role==='patient_insight'){document.getElementById('month-recap').hidden=!allClaims.length;document.getElementById('recap-placeholder').hidden=true;document.getElementById('home-view').classList.toggle('has-recap',Boolean(allClaims.length));for(const selector of openDisclosures){const fold=area.querySelector(selector);if(fold)fold.open=true;}}
  }
  function valid(ticket,ctx){const latest=window.auraAgentContext();return ticket===requestEpoch&&latest.patientId===ctx.patientId&&latest.role===ctx.role&&!latest.offline&&navigator.onLine;}
  async function arrival(){
    const ctx=window.auraAgentContext();if(!ctx.patientId||!ctx.record||document.body.dataset.page==='about')return;
    const role=ctx.role==='clinician'?'clinician_brief':'patient_insight',area=document.getElementById(`agent-${role}`),ticket=requestEpoch;
    if(ctx.offline||!navigator.onLine){area.replaceChildren(node('p','Assessment paused while offline. Safety resources remain separate.'));return;}
    if(role==='patient_insight'&&!area.querySelector('.patient-recap'))document.getElementById('recap-placeholder').hidden=false;
    const key=`${ctx.patientId}:${role}:${ctx.revision}`;
    if(pending.has(key))return pending.get(key);
    const work=(async()=>{
      const response=await fetch(`/patients/${encodeURIComponent(ctx.patientId)}/assessment/${role}`,{cache:'no-store'});const arrival=await response.json();
      if(!valid(ticket,ctx))return;if(!response.ok)throw new Error(arrival.error?.message||'Assessment unavailable');
      render(arrival.cached||arrival.preview,area,role);
      if(role==='patient_insight'&&arrival.preview.draft.claims.length)document.getElementById('month-recap').hidden=false;
      if(!arrival.generation_allowed||arrival.cached||completed.has(arrival.run_id)||(role==='patient_insight'&&!arrival.preview.draft.claims.length))return;
      completed.set(arrival.run_id,true);
      const generated=await fetch(`/patients/${encodeURIComponent(ctx.patientId)}/agent/${role}`,{method:'POST',headers:{'Content-Type':'application/json'},cache:'no-store',body:JSON.stringify({run_id:arrival.run_id,window_days:arrival.window_days,client_offline:false})});
      const result=await generated.json();if(!valid(ticket,ctx))return;
      if(generated.ok&&result.status!=='STALE')render(result,area,role);
    })().catch(()=>{ /* Immediate extraction remains visible; no retry loop. */ }).finally(()=>{pending.delete(key);if(ticket!==requestEpoch)arrival();});pending.set(key,work);return work;
  }
  window.refreshAuraAssessment=arrival;
  // Chart backlinks must reveal a card nested in the one-tap overflow first.
  document.addEventListener('click',event=>{
    const link=event.target.closest?.('a[href^="#story-finding-"]');if(!link)return;
    const target=document.getElementById(link.getAttribute('href').slice(1));
    for(let parent=target?.parentElement;parent;parent=parent.parentElement)if(parent.tagName==='DETAILS')parent.open=true;
  },true);
  document.addEventListener('click',async event=>{
    const trigger=event.target.closest('[data-agent-role]');if(!trigger)return;
    const ctx=window.auraAgentContext(),role=trigger.dataset.agentRole,area=document.getElementById(`agent-${role}`);
    if(['clinician_brief','patient_insight'].includes(role)){await arrival();return;}
    if(!ctx.patientId||ctx.offline||!navigator.onLine)return;
    const ticket=requestEpoch;trigger.disabled=true;area.replaceChildren(node('p','Reading the recorded evidence…'));
    try{
      const question=role==='record_qa'?document.getElementById('agent-question-text')?.value.trim()||null:null;
      const response=await fetch(`/patients/${encodeURIComponent(ctx.patientId)}/agent/${role}`,{method:'POST',headers:{'Content-Type':'application/json'},cache:'no-store',body:JSON.stringify({run_id:window.auraUniqueId(),window_days:56,query_id:role==='record_qa'&&!question?document.getElementById('agent-query').value:null,question,client_offline:false})});
      const result=await response.json();if(!valid(ticket,ctx))return;if(!response.ok)throw new Error(result.error?.message||'Assistant unavailable');
      if(question)await refresh();
      const latest=window.auraAgentContext(),displayEpoch=requestEpoch;if(latest.patientId!==ctx.patientId||latest.role!==ctx.role||latest.offline)return;
      // The gated question may have committed stronger safety state. Recheck the
      // server approval before displaying any otherwise ordinary answer.
      const guardResponse=await fetch(`/patients/${encodeURIComponent(ctx.patientId)}/assessment/clinician_brief`,{cache:'no-store'}),guard=await guardResponse.json();
      if(!valid(displayEpoch,latest)||!guardResponse.ok)return;
      if(!guard.generation_allowed||guard.state_fingerprint!==result.state_fingerprint){area.replaceChildren(node('p','Safety interaction or a changed record takes priority.'));return;}render(result,area,role);
    }catch(error){if(ticket===requestEpoch)area.replaceChildren(node('p',error.message));}finally{trigger.disabled=false;}
  });
  window.addEventListener('aura-record-view',()=>{
    const ctx=window.auraAgentContext(),key=`${ctx.patientId}:${ctx.revision}:${ctx.offline}:${ctx.role}`;
    if(key!==identity){identity=key;requestEpoch++;for(const id of ['agent-clinician_brief','agent-patient_insight','agent-record_qa','agent-question_ranker','agent-visit_prep','assessment-complete']){const area=document.getElementById(id);if(area){rendered.delete(area);area.replaceChildren();}}window.clearAuraStory?.();}
    for(const trigger of document.querySelectorAll('[data-agent-role]'))trigger.disabled=ctx.offline;
    arrival();
  });
})();
