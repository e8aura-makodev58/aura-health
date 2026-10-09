/* Read-only presentation. Existing server guards own generation permission. */
"use strict";
(() => {
  const node=(tag,text,cls)=>{const e=document.createElement(tag);if(text!=null)e.textContent=text;if(cls)e.className=cls;return e;};
  let identity='',requestEpoch=0; const pending=new Map(), completed=new Map(), priorLines=new Map();
  const prep=node('section',null,'card agent-card');prep.append(node('h2','Your visit note'),node('p','Choose what to bring. Not sent.','fine'));
  const button=node('button','Help prepare my note');button.dataset.agentRole='visit_prep';
  const output=node('div');output.id='agent-visit_prep';output.setAttribute('aria-live','polite');prep.append(button,output);document.getElementById('appointment-preview').before(prep);
  const icons={SLEEP_MIDPOINT:'☾',SLEEP_DURATION:'☾',ACTIVITY:'↟',RESTING_HEART_RATE:'♡',HEART_RATE_VARIABILITY:'♡',RESPIRATORY_RATE:'≋'};
  const titles={SLEEP_MIDPOINT:'Sleep timing',SLEEP_DURATION:'Sleep duration',ACTIVITY:'Activity',RESTING_HEART_RATE:'Resting heart rate'};
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
    const direction={LATER:'later',EARLIER:'earlier',HIGHER:'higher',LOWER:'lower'}[finding.direction];
    if(!direction)return null;
    const amount=Number.isFinite(delta)?Math.abs(delta):null;
    let magnitude=`${direction} than your usual`;
    if(amount!==null){
      const formatted=signal.unit.startsWith('minutes')?(amount>=60?`${Math.round(amount/60*2)/2} h`:`${Math.round(amount)} min`):
        signal.key.signal==='ACTIVITY'&&['steps','step'].includes(signal.unit)?`${new Intl.NumberFormat('en-GB').format(Math.round(amount/100)*100)} steps a day`:
        `${new Intl.NumberFormat('en-GB',{maximumFractionDigits:1}).format(amount)} ${signal.unit}`;
      // A small nonzero value must not be displayed as an apparent zero change.
      if(amount>0&&!/^0(?: |\.0 )/.test(formatted))magnitude=`about ${formatted} ${signal.key.signal==='ACTIVITY'?(delta<0?'fewer':'more'):direction}`;
    }
    const label=titles[finding.signal]||signal.label,wording=finding.signal==='SLEEP_MIDPOINT'?`Sleeping ${direction} than usual`:`${label} ${direction} than usual`;
    return {label,icon:icons[finding.signal]||'◌',magnitude,wording,delta,unit:signal.unit,since:finding.since,until:fact.at,
      line:`${direction[0].toUpperCase()+direction.slice(1)} than usual · ${date(finding.since)}–${date(fact.at)}`,
      source:fact.source_ref,method:row.drift.kind==='TRANSIENT_DEVIATION'?'Current versus recent rolling reference':'Recent rolling reference versus your usual',
      recordStart:record.period.start?.slice(0,10),recordEnd:record.period.end?.slice(0,10)};
  }
  function findingCard(claim,result,role,number){
    const finding=claim.findings?.[0],display=finding&&presentation(finding,result.sources);
    if(!display)return null;
    const patient=role==='patient_insight',card=node('section',null,`agent-claim finding-card ${patient?'patient-finding':'clinician-finding'}`);
    card.dataset.signal=finding.signal;card.dataset.source=display.source;
    const header=node('div',null,'finding-card-heading'),icon=node('span',display.icon,'signal-icon');icon.setAttribute('aria-hidden','true');
    header.append(icon,node('h4',patient?display.wording:display.label));
    if(!patient){card.id=`story-finding-${number}`;card.tabIndex=-1;header.append(node('span',String(number),'finding-number'));}
    const show=node('button',patient?'Why? / Sources':'Why?','text-button finding-why');show.type='button';show.setAttribute('aria-expanded','false');header.append(show);card.append(header);
    if(patient){card.append(node('p',`Since ${everydayDate(display.since)}`,'finding-date'),node('span','shifted','badge finding-state'));}
    else{
      card.append(node('p',`${['LOWER','EARLIER'].includes(finding.direction)?'↓':'↑'} ${display.magnitude}`,'finding-magnitude'));
      const span=node('div',null,'finding-span');span.dataset.since=display.since;span.dataset.until=display.until;span.setAttribute('aria-label',`Recorded span ${date(display.since)} to ${date(display.until)}`);
      span.append(node('span'));card.append(span,node('p',display.line,'finding-one-liner'));
    }
    const detail=node('section',null,'claim-sources finding-detail');detail.hidden=true;detail.id=`finding-detail-${role}-${number}`;show.setAttribute('aria-controls',detail.id);
    detail.append(node('p',patient?`${display.wording}, in the recorded dates shown here. This is an observation, not a conclusion about mental health.`:display.method,'finding-method'));
    if(!patient&&Number.isFinite(display.delta))detail.append(node('p',`Exact stored deviation: ${display.delta} ${display.unit}. Compared with your usual or recent reference as labelled above.`,'fine'));
    for(const id of claim.fact_ids){const fact=result.sources.find(f=>f.fact_id===id);if(fact)detail.append(node('p',`${fact.text} Source: ${fact.source_ref}.`,'fine'));}
    show.addEventListener('click',()=>{detail.hidden=!detail.hidden;show.setAttribute('aria-expanded',String(!detail.hidden));});card.append(detail);
    if(patient)card.addEventListener('click',event=>{if(!event.target.closest('button,a')&&!detail.contains(event.target))show.click();});
    return {card,link:{...finding,number,target_id:card.id,callout:display.line}};
  }
  function steadyCard(record){
    // Explicit repeated patient reports, not a new clinical/sensor stability classifier.
    const cutoff=record?.period.end?Date.parse(record.period.end.slice(0,10))-29*86400000:Infinity;
    const rows=(record?.checkins||[]).filter(row=>!row.deferred&&Date.parse(row.at.slice(0,10))>=cutoff).slice(-3);
    if(rows.length<2||rows.some(row=>row.state!==rows[0].state))return null;
    const card=node('section',null,'agent-claim finding-card patient-finding steady-report'),header=node('div',null,'finding-card-heading');
    header.append(node('span','◌','signal-icon'),node('h4',`Recent check-ins: ${rows[0].state}`));card.append(header,node('span','steady · reports','badge finding-state'));
    const detail=node('div',null,'claim-sources');detail.hidden=true;detail.append(node('p',`Your last ${rows.length} recorded check-ins used the same answer. This describes your reports, not an assessment of your health.`));
    for(const row of rows)detail.append(node('p',`${date(row.at)} · ${row.state}. Source: ${row.event_id}.`,'fine'));
    const show=node('button','Why? / Sources','text-button');show.setAttribute('aria-expanded','false');show.addEventListener('click',()=>{detail.hidden=!detail.hidden;show.setAttribute('aria-expanded',String(!detail.hidden));});card.append(show,detail);return card;
  }
  function render(result,area,role){
    const previous=priorLines.get(role)||new Set(), now=new Set();area.replaceChildren();
    const paused=result.status==='BLOCKED'||result.status==='STALE';
    const label=paused?'Assessment paused':result.generation_used?result.extracted_fact_ids?.length?'Checked AI + source extraction':'AI-written · sources checked':'Offline extraction';
    const chip=node('span',label,'agent-disclosure badge');chip.title=result.disclosure;area.append(chip);
    if(paused){document.getElementById('assessment-complete')?.replaceChildren();window.clearAuraStory?.();document.getElementById('agent-visit_prep')?.replaceChildren();area.append(node('p','Safety interaction or record evaluation comes first. See the separate safety panel.'));return;}
    if(result.draft.headline&&role!=='patient_insight')area.append(node('h3',result.draft.headline.split(/\s+/).slice(0,20).join(' ')));
    const allClaims=result.draft.claims||[], displayed=['clinician_brief','patient_insight'].includes(role)?allClaims.slice(0,role==='patient_insight'?2:3):allClaims;
    const linkage=[],grid=node('div',null,'finding-grid');let number=0;area.append(grid);
    for(const claim of displayed){
      const key=JSON.stringify([claim.text,claim.findings,claim.fact_ids.map(id=>result.sources.find(f=>f.fact_id===id)?.source_ref)]);now.add(key);
      const shaped=['clinician_brief','patient_insight'].includes(role)&&findingCard(claim,result,role,number+1);
      if(shaped){number++;if(previous.size&&!previous.has(key))shaped.card.classList.add('assessment-changed');grid.append(shaped.card);if(role==='clinician_brief')linkage.push(shaped.link);continue;}
      const line=node('section',null,'agent-claim');if(previous.size&&!previous.has(key))line.classList.add('assessment-changed');
      if(role==='clinician_brief'&&claim.findings?.length){number++;line.id=`story-finding-${number}`;line.tabIndex=-1;line.append(node('span',String(number),'finding-number'));for(const finding of claim.findings)linkage.push({...finding,number,target_id:line.id});}
      line.append(node('p',claim.text));
      if(role==='clinician_brief')for(const finding of claim.findings||[]){
        const origin=result.sources.find(f=>f.fact_id===finding.fact_id);
        const metric=result.sources.find(f=>f.source_ref===origin?.source_ref&&f.signal===finding.signal&&!f.finding&&/deviation/.test(f.text));
        if(metric&&!claim.text.includes(metric.text)){
          const deviation=metric.text.match(/rolling versus own reference deviation ([^;]+);?/);
          line.append(node('p',`${deviation?`Compared with your usual: ${deviation[1]}`:metric.text} · Source extraction`,'fine'));
        }
      }
      if(claim.fact_ids.some(id=>(result.extracted_fact_ids||[]).includes(id)))line.append(node('span','Source extraction','fine'));
      const sources=node('div',null,'claim-sources');sources.hidden=true;
      for(const id of claim.fact_ids){const fact=result.sources.find(f=>f.fact_id===id);if(fact)sources.append(node('p',`${fact.text} Source: ${fact.source_ref}.`,'fine'));}
      const show=node('button','Sources','text-button');show.setAttribute('aria-expanded','false');show.addEventListener('click',()=>{sources.hidden=!sources.hidden;show.setAttribute('aria-expanded',String(!sources.hidden));});line.append(show,sources);
      if(role==='visit_prep'){const remove=node('button','Remove from this preview','text-button');remove.addEventListener('click',()=>line.remove());line.append(remove);}area.append(line);
    }
    if(role==='patient_insight'&&allClaims.length){const steady=steadyCard(window.auraAgentContext().record);if(steady)grid.append(steady);}
    priorLines.set(role,now);
    if(role==='clinician_brief'){
      for(const [title,kind,empty] of [['Context recorded','get_context','No associated context in these facts.'],['Data gaps','get_gaps','No gaps in the retrieved facts.']]){
        const facts=result.sources.filter(f=>kind==='get_gaps'?/SENSING_GAP|SENSING_RETURN/.test(f.text):/context recorded|patient-reported context/.test(f.text));
        if(!facts.length)continue;
        const group=node('section',null,'assessment-subsection');group.append(node('h4',title));
        for(const fact of facts.slice(0,2))group.append(node('p',fact.text,'fine'));area.append(group);
      }
      const questions=node('section');questions.append(node('h4','Worth asking'));
      if(result.draft.question_ids?.length)area.append(questions);
      const complete=document.getElementById('assessment-complete');if(complete){complete.replaceChildren(node('h3','Complete sourced assessment'));for(const c of allClaims)complete.append(node('p',c.text));for(const f of result.sources)complete.append(node('p',`${f.fact_id} · ${f.text} · Source: ${f.source_ref}`,'fine'));}
      window.linkAuraStoryFindings?.(linkage,result.sources);
      window.setAuraComparisonAssessment?.(result);
    }
    for(const id of result.draft.question_ids||[]){const text=result.question_options[id];if(!text)continue;const copy=node('button',text,'agent-question question-copy');copy.type='button';copy.title='Copy this approved question';copy.addEventListener('click',async()=>{try{await navigator.clipboard.writeText(text);copy.setAttribute('aria-label',`${text} — copied`);}catch{const input=document.getElementById('agent-question-text');input.value=text;input.focus();}});area.append(copy);}
    if(!allClaims.length&&!result.draft.question_ids?.length)area.append(node('p','Nothing additional to highlight from these records.'));
    const trace=node('section',null,'agent-trace');trace.hidden=true;
    trace.append(node('p',`Run ${result.run_id} · ${result.model_id||'not called'} · ${result.reason} · ${result.elapsed_ms||0} ms`,'fine'));
    for(const entry of result.trace||[])trace.append(node('p',entry.tool?`${entry.tool}: ${(entry.fact_ids||[]).length} linked facts`:entry.action,'fine'));
    if(role!=='patient_insight'){const showTrace=node('button','Inspect assistant steps','text-button');showTrace.addEventListener('click',()=>{trace.hidden=!trace.hidden;});area.append(showTrace,trace);}
    if(role==='patient_insight'){document.getElementById('month-recap').hidden=!allClaims.length;document.getElementById('home-view').classList.toggle('has-recap',Boolean(allClaims.length));}
  }
  function valid(ticket,ctx){const latest=window.auraAgentContext();return ticket===requestEpoch&&latest.patientId===ctx.patientId&&latest.role===ctx.role&&!latest.offline&&navigator.onLine;}
  async function arrival(){
    const ctx=window.auraAgentContext();if(!ctx.patientId||!ctx.record||document.body.dataset.page==='about')return;
    const role=ctx.role==='clinician'?'clinician_brief':'patient_insight',area=document.getElementById(`agent-${role}`),ticket=requestEpoch;
    if(ctx.offline||!navigator.onLine){area.replaceChildren(node('p','Assessment paused while offline. Safety resources remain separate.'));return;}
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
    if(key!==identity){identity=key;requestEpoch++;for(const id of ['agent-clinician_brief','agent-patient_insight','agent-record_qa','agent-question_ranker','agent-visit_prep','assessment-complete'])document.getElementById(id)?.replaceChildren();window.clearAuraStory?.();}
    for(const trigger of document.querySelectorAll('[data-agent-role]'))trigger.disabled=ctx.offline;
    arrival();
  });
})();
