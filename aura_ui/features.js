/* Synthetic workflow controls. Presentation only; server validates every command. */
'use strict';
(() => {
  const byId=id=>document.getElementById(id);
  const el=(tag,text,cls)=>{const n=document.createElement(tag);if(text!=null)n.textContent=text;if(cls)n.className=cls;return n;};
  const notice=byId('notice');
  let working=false,proposal=null,contextProposal=null,lastRun=null,loadedPatient=null;
  function report(text,error=false){notice.hidden=false;notice.textContent=text;notice.classList.toggle('error',error);}
  async function call(action,data,runId=window.auraUniqueId()){
    const ctx=window.auraAgentContext();
    if(!ctx.patientId||ctx.offline||!navigator.onLine)throw new Error('Reconnect before submitting. Safety resources remain available.');
    const response=await fetch(`/patients/${encodeURIComponent(ctx.patientId)}/workflows/${action}`,{method:'POST',headers:{'Content-Type':'application/json'},cache:'no-store',body:JSON.stringify({run_id:runId,data})});
    const result=await response.json();if(!response.ok)throw new Error(result.error?.message||'Workflow unavailable');
    if(window.auraAgentContext().patientId!==ctx.patientId)throw new Error('Record changed; reload this record to inspect the saved result.');
    return result;
  }
  async function work(fn){if(working)return;working=true;for(const b of document.querySelectorAll('[data-workflow]'))b.disabled=true;try{await fn();}catch(e){report(e.message,true);}finally{working=false;for(const b of document.querySelectorAll('[data-workflow]'))b.disabled=false;}}
  async function reload(){await refresh();window.dispatchEvent(new CustomEvent('aura-input-committed'));}
  function button(text,fn){const b=el('button',text);b.type='button';b.dataset.workflow='true';b.addEventListener('click',()=>work(fn));return b;}
  function labelled(parent,text,input){const label=el('label',text);parent.append(label,input);return input;}
  function input(type,id){const n=el('input');n.type=type;n.id=id;return n;}

  // Consolidated scope page. Functional state/AI source and pinned safety remain.
  const link=document.querySelector('.info-link');link.textContent='Disclaimer';link.href='#disclaimer';link.setAttribute('aria-label','Disclaimer and demonstration limits');
  byId('about-heading').textContent='Disclaimer';
  const about=byId('about-view').querySelector('.card');
  const privacy=byId('privacy-notice');about.replaceChildren(el('h2','Technical demonstration'),el('p','AURA is a technical proposal for a sponsor to assess for clinical and regulatory suitability. This demonstration uses synthetic data only, with no clinical validation claimed.'),el('h2','Intended use'),el('p','For adults aged 25–60 on stable clinician-managed antidepressant maintenance treatment. AURA organizes longitudinal information and medication routines and prepares patient-controlled review context. It does not diagnose depression, predict relapse, prescribe or modify treatment, provide psychotherapy, determine suicide risk, replace a clinician, or operate as an emergency monitoring service.'),el('h2','AI and deployment'),privacy,el('p','The live model receives synthetic records. Future medical-institution use is intended for an institution-managed on-premises or private-cloud model, subject to the sponsor’s review. Generation cannot own safety state or anchors. Unavailable or rejected outputs use transparent extraction or fixed fallback.'),el('h2','Engineering limits'),el('p','Windows, thresholds, signal enablement, contextual associations and synthetic physiological effects are engineering settings, not clinical thresholds. Context association is explicitly confirmed, not established medical causation. There is no governed automatic exit from REESTABLISHING. Sparse channels are never interpolated.'),el('h2','Safety and access'),el('p','Pinned safety information remains available independently. Current contacts and question wording are development fixtures requiring sponsor review. There is no emergency monitoring, production authentication, automatic clinician transmission or real wearable ingestion. Review previews are Not sent; patient approval and sharing are future work.'),el('h2','Synthetic clinician view'),el('p','The demo exposes the full synthetic record for inspection. A real clinician would see only information approved by the patient. Hosted workspaces are separate demonstration sessions, not authenticated patient records.'));
  const demoTag=el('a','Demo');demoTag.href='#disclaimer';document.querySelector('.demo-bar>span').replaceWith(demoTag);
  document.querySelector('#clinician-disclosure').replaceChildren(el('strong','Clinician view · Demo'));
  byId('held-section').querySelector(':scope>p').remove();
  byId('workspace-safety').querySelector('.summary-caption').textContent='Recorded episodes';
  byId('routine-saved').textContent='Your recorded routine';
  byId('review-view').querySelector('.sharing-note strong').textContent='Not sent';
  byId('review-view').querySelector('.sharing-note p').textContent='Choose what you want to bring to your appointment.';
  byId('explanation-fields').querySelector('p.fine').remove();
  byId('why-heading').textContent='Why AURA asked';
  for(const p of byId('demo-panel').querySelectorAll(':scope>p'))if(p.id!=='hosted-notice')p.remove();
  const disclaimerLink=el('a','Demonstration limits');disclaimerLink.href='#disclaimer';byId('demo-panel').prepend(disclaimerLink);
  const question=input('text','agent-question-text');question.maxLength=2000;question.placeholder='e.g. Did sleep timing change before the travel note?';
  const qaLabel=el('label','Ask about this record');qaLabel.htmlFor='agent-question-text';byId('agent-query').before(qaLabel,question);
  byId('agent-query').after(el('p','Or choose a quick question','fine'));
  for(const p of byId('agent-workspace').querySelectorAll('p.fine'))if(p.textContent.includes('Selected record'))p.remove();
  byId('agent-workspace').querySelector(':scope>p:not(.eyebrow)').textContent='What changed, what was reported, and what remains worth asking.';
  byId('dialog-privacy').textContent='Safety evaluation comes first. An unavailable evaluation holds the note.';
  byId('why-dialog').querySelector(':scope>p.fine').remove();
  const copy=el('p','Synthetic input only','fine');byId('input-text').before(copy);
  // Context proposal and explicit confirmation. No automatic credibility decision.
  const contextActions=el('section',null,'card workflow-card');contextActions.append(el('h2','Add context to a change'));
  const text=labelled(contextActions,'Your synthetic explanation',el('textarea'));text.rows=3;text.maxLength=2000;
  const contextConfirm=el('div');contextConfirm.hidden=true;
  const category=el('select');for(const name of ['BENIGN_CONTEXT','RISK_CONTEXT']){const option=el('option',name==='BENIGN_CONTEXT'?'Benign context':'Risk context — do not explain away');option.value=name;category.append(option);}
  labelled(contextConfirm,'Category',category);const signals=el('div');contextConfirm.append(signals);
  contextActions.append(button('Suggest related observations',async()=>{
    contextProposal=await call('context-proposal',{text:text.value.trim()});category.value=contextProposal.proposal.category;
    category.disabled=category.value==='RISK_CONTEXT';signals.replaceChildren();
    for(const s of signalCatalog){const row=el('label');const check=input('checkbox');check.value=s.name;check.checked=contextProposal.proposal.affected_signals.includes(s.name);row.append(check,el('span',s.label));signals.append(row);}
    contextConfirm.hidden=false;report('Check the category and explicitly select the related observations.');await reload();
  }),contextConfirm);
  contextConfirm.append(button('Keep this context for review',async()=>{
    await call('context-confirm',{proposal_id:contextProposal.run_id,category:category.value,affected_signals:[...signals.querySelectorAll('input:checked')].map(c=>c.value),confirm:'KEEP_EXPLICIT_CONTEXT'});
    contextConfirm.hidden=true;text.value='';await reload();report('Context retained. Your own reference has not been changed.');
  }));
  const contextDetails=el('details',null,'card');contextDetails.append(el('summary','Add a contextual explanation'),contextActions);byId('context-list').parentElement.after(contextDetails);

  // Structured manual measurements and user-confirmed CSV / JSON mapping.
  const intake=el('details',null,'card workflow-card');intake.id='manual-intake';intake.append(el('summary','Record or import measurements'));
  const manual=el('form');manual.id='manual-form';const day=labelled(manual,'Recorded date',input('date','measurement-date'));const fields=el('div',null,'measurement-fields');manual.append(fields);
  const save=el('button','Save measurements','primary');save.type='submit';save.dataset.workflow='true';manual.append(save);intake.append(manual);
  manual.addEventListener('submit',e=>{e.preventDefault();work(async()=>{const values={};for(const field of fields.querySelectorAll('input'))if(field.value!=='')values[field.dataset.signal]=Number(field.value);await call('manual',{day:day.value,values});await reload();report('Measurements recorded. Missing fields were omitted.');});});
  const imports=el('details');imports.append(el('summary','Import synthetic CSV or JSON'));
  const file=input('file','import-file');file.accept='.csv,.json';imports.append(file);
  const content=labelled(imports,'Or paste synthetic rows',el('textarea'));content.rows=4;content.maxLength=110000;content.placeholder='date,RESTING_HEART_RATE\n2026-03-12,66';
  file.addEventListener('change',async()=>{if(file.files[0]?.size>110000){report('File exceeds 110 KB',true);return;}if(file.files[0])content.value=await file.files[0].text();});
  const mapping=el('textarea');mapping.rows=6;mapping.id='import-mapping';mapping.hidden=true;
  const confirm=button('Confirm mapping and import',async()=>{await call('import-confirm',{proposal_id:proposal.run_id,mapping:JSON.parse(mapping.value),confirm:'IMPORT_SYNTHETIC_DATA'});confirm.hidden=true;mapping.hidden=true;await reload();report('Import committed. No unit conversion or missing-value filling was performed.');});confirm.hidden=true;
  imports.append(button('Propose column mapping',async()=>{const format=content.value.trim().startsWith('[')?'json':'csv';proposal=await call('import-proposal',{format,content:content.value});mapping.value=JSON.stringify(proposal.mapping,null,2);mapping.hidden=false;confirm.hidden=false;report('Review column, signal and exact unit mappings before importing.');}),mapping,confirm);intake.append(imports);byId('recorded-details').before(intake);
  let signalCatalog=[];
  fetch('/signals').then(r=>r.json()).then(data=>{signalCatalog=data.signals;for(const s of signalCatalog){const field=input('number');field.step='any';field.dataset.signal=s.name;labelled(fields,`${s.label} (${s.name==='ACTIVITY'?'steps':s.unit})`,field);}}).catch(()=>report('Measurement registry unavailable',true));

  // Demo guide is the ONLY home of the life director controls.
  const sim=el('section',null,'simulator-controls');sim.id='life-director';sim.append(el('h2','Advance this synthetic life'));
  const auto=input('checkbox','auto-assessment');auto.checked=true;const autoLabel=el('label');autoLabel.append(auto,el('span','Refresh AI brief after a committed input'));sim.append(autoLabel);
  window.addEventListener('aura-input-committed',()=>{if(auto.checked){const role=window.auraAgentContext().role==='clinician'?'clinician_brief':'patient_insight';document.querySelector(`[data-agent-role="${role}"]`)?.click();}});
  const request=labelled(sim,'What happens next?',el('textarea'));request.rows=2;request.maxLength=2000;request.placeholder='e.g. three days of flu, or a week away from the wearable';
  const seed=labelled(sim,'Random seed',input('number','sim-seed'));seed.value='7';seed.min='0';seed.max='2147483647';
  const notes=input('checkbox','sim-feedback');notes.checked=true;const notesLabel=el('label');notesLabel.append(notes,el('span','Simulated feedback: check-ins, routine and safety-gated notes'));sim.append(notesLabel);
  const quick=el('div',null,'settings-actions');for(const theme of ['Flu','Travel','Work stress','Alcohol','Missed medication','Wearable off','Exercise'])quick.append(button(theme,async()=>{request.value=theme;}));sim.append(quick);
  const advances=el('div',null,'settings-actions');const trace=el('details');trace.append(el('summary','Inspect last simulator run'));const traceBody=el('pre');trace.append(traceBody);
  for(const days of [1,3,7])advances.append(button(`Advance ${days} day${days>1?'s':''}`,async()=>{
    report('Planning synthetic life events and generating measurements…');lastRun=await call('advance',{days,seed:Number(seed.value),request:request.value,notes:notes.checked});
    traceBody.textContent=JSON.stringify({run_id:lastRun.run_id,status:lastRun.status,plan:lastRun.plan,event_count:lastRun.event_ids.length,seed:lastRun.seed,config:lastRun.effects.version},null,2);
    await reload();report(`Advanced ${days} days. ${lastRun.event_ids.length} events recorded.`);
  }));sim.append(advances,trace);
  sim.append(button('Verify deterministic replay',async()=>{if(!lastRun)throw new Error('Advance the life first');const response=await fetch(`/patients/${encodeURIComponent(window.auraAgentContext().patientId)}/simulator-runs/${lastRun.run_id}/replay`);const result=await response.json();if(!response.ok)throw new Error(result.error?.message||'Replay failed');report(result.matched?`Replay matched all ${result.days} generated days exactly; no state written.`:'Replay mismatch',!result.matched);}),button('Save trace',async()=>{if(!lastRun)throw new Error('Advance the life first');const blob=new Blob([JSON.stringify(lastRun,null,2)],{type:'application/json'});const a=el('a');a.href=URL.createObjectURL(blob);a.download='aura-simulator-trace.json';a.click();setTimeout(()=>URL.revokeObjectURL(a.href),1000);}));byId('demo-panel').append(sim);
  const print=button('Print / save visit pack',async()=>{location.hash='review';document.body.classList.add('printing-review');window.print();document.body.classList.remove('printing-review');});print.id='print-visit-pack';byId('review-view').append(print);
  window.addEventListener('aura-record-view',()=>{const ctx=window.auraAgentContext();if(ctx.patientId!==loadedPatient){loadedPatient=ctx.patientId;proposal=contextProposal=lastRun=null;contextConfirm.hidden=true;mapping.hidden=confirm.hidden=true;traceBody.textContent='';}if(ctx.record?.period.end)day.value=ctx.record.period.end.slice(0,10);});
})();
