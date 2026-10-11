/* I9 deterministic presentation fixtures. No provider calls or domain computation. */
'use strict';
const assert=require('node:assert/strict'),path=require('node:path');
const {chromium}=require('playwright');
(async()=>{
 const browser=await chromium.launch({headless:true}),page=await browser.newPage({viewport:{width:390,height:844}}),errors=[];
 page.on('pageerror',e=>errors.push(e.message));
 try{
  await page.setContent('<section id="home-view"><section id="month-recap"><div id="agent-patient_insight"></div></section></section><div id="agent-clinician_brief"></div><div id="agent-record_qa"></div><div id="agent-question_ranker"></div><div id="assessment-complete"></div><section id="appointment-preview"></section>');
  await page.addStyleTag({path:path.resolve('aura_ui/evidence.css')});
  await page.evaluate(()=>{
   const finding={signal:'SLEEP_MIDPOINT',direction:'LATER',since:'2026-02-23'};
   const row={first_seen:'2026-02-23',last_seen:'2026-03-11',event_id:'sleep-event',drift:{kind:'PERSISTENT_DRIFT',rolling_vs_anchor:195.423456,current_vs_rolling:7}};
   window.ctx={patientId:'synthetic',revision:1,role:'clinician',offline:false,record:{period:{start:'2026-01-01',end:'2026-03-11'},signals:[{key:{signal:'SLEEP_MIDPOINT',source:'watch',metric:''},label:'Sleep timing',unit:'minutes since sleep-start midnight',findings:[row]}],checkins:[{state:'Good',at:'2026-03-10',event_id:'checkin-1'},{state:'Good',at:'2026-03-11',event_id:'checkin-2'}]}};
   window.auraAgentContext=()=>window.ctx;
   window.auraUniqueId=()=> 'unused';window.linkAuraStoryFindings=items=>window.linked=items;window.clearAuraStory=()=>{window.linked=[];};
   window.result={status:'COMPLETE',generation_used:false,draft:{headline:'Recorded changes',claims:[{text:'Exact source: 195.423456 minutes',fact_ids:['f1'],findings:[{fact_id:'f1',...finding}]}],question_ids:[]},sources:[{fact_id:'f1',source_ref:'sleep-event',text:'Exact source: 195.423456 minutes',finding,at:'2026-03-11'}],question_options:{},trace:[]};
   result.record_presentation={checkins:{text:'Patient-reported: Good on 2 recorded days.',checkin_summary:{state:'Good',count:2,window_days:7,run_days:2,run_start:'2026-03-10',source_refs:['checkin-1','checkin-2']}}};
   window.fetch=async()=>({ok:true,json:async()=>({preview:window.result,run_id:'fixture',generation_allowed:false})});
  });
  await page.addScriptTag({path:path.resolve('aura_ui/agent.js')});
  await page.evaluate(()=>dispatchEvent(new Event('aura-record-view')));await page.waitForSelector('.clinician-finding');
  assert.match(await page.locator('.finding-magnitude').innerText(),/about 3\.5 h later/);
  assert.doesNotMatch(await page.locator('#agent-clinician_brief').innerText(),/195\.423|2026-02/);
  assert.equal(await page.evaluate(()=>linked[0].callout),'Later than usual · 23 Feb–11 Mar');
  await page.locator('.finding-why').click();assert.match(await page.locator('.finding-detail').innerText(),/195\.423456 minutes.*Source: sleep-event/s);
  assert.equal(await page.locator('.finding-why').getAttribute('aria-expanded'),'true');
  console.log('I9_ROUNDED_CARD_EXACT_COMMITTED_EVIDENCE PASS');
  await page.evaluate(()=>{ctx.role='patient';dispatchEvent(new Event('aura-record-view'));});await page.waitForSelector('.patient-recap');
  assert.match(await page.locator('.patient-recap').innerText(),/sleep time was later than usual/i);
  assert.equal(await page.locator('.patient-finding').isVisible(),false);
  assert.equal(await page.locator('.patient-checkins').isVisible(),false);
  await page.locator('.patient-summary-details > summary').click();
  assert.match(await page.locator('#agent-patient_insight').innerText(),/Sleeping later than usual.*late February.*shifted/s);
  assert.doesNotMatch(await page.locator('#agent-patient_insight').innerText(),/\d{4}-\d{2}-\d{2}|Recorded changes|195\.423/);
  assert.match(await page.locator('.patient-checkins').innerText(),/Recent check-ins: Good.*2 of the last 7 days/s);
  assert.doesNotMatch(await page.locator('.patient-checkins').innerText(),/steady/);
  await page.locator('.patient-finding .finding-why').click();
  await page.locator('.patient-checkins summary').click();
  assert.doesNotMatch(await page.locator('#agent-patient_insight').innerText(),/not a conclusion|not an assessment|not a diagnosis|assessment of your health/i);
  assert.match(await page.locator('.patient-checkins details').innerText(),/Good on 2 recorded days.*checkin-1.*checkin-2/s);
  assert.equal(await page.locator('#home-view svg').count(),0);
  await page.evaluate(()=>{ctx.record.checkins=[];result.record_presentation.checkins=null;ctx.revision++;dispatchEvent(new Event('aura-record-view'));});await page.waitForTimeout(100);
  assert.equal(await page.locator('.patient-checkins').count(),0);
  console.log('I9_PATIENT_PLAIN_CARDS_NO_FABRICATED_STEADY PASS');
  await page.evaluate(()=>{
   result.generation_used=true;result.draft.headline='Your sleep time was later than usual in these records.';result.headline_fact_ids=['f1'];
   result.sources.push({fact_id:'unrelated',source_ref:'other-event',text:'Unrelated retained record: 72 bpm.'});
   ctx.revision++;dispatchEvent(new Event('aura-record-view'));
  });
  await page.waitForFunction(()=>document.querySelector('.patient-recap')?.textContent==='Your sleep time was later than usual in these records.');
  assert.equal(await page.locator('.patient-finding').isVisible(),false);
  assert.equal(await page.locator('.patient-summary-sources .agent-disclosure').isVisible(),false);
  assert.doesNotMatch(await page.locator('#agent-patient_insight').innerText(),/72 bpm|195\.423456|AI-written/);
  await page.locator('.patient-summary-sources > summary').click();
  assert.match(await page.locator('.patient-recap-source').innerText(),/195\.423456.*Source: sleep-event/s);
  assert.equal(await page.locator('.patient-recap-source').count(),1);
  assert.doesNotMatch(await page.locator('.patient-summary-sources').innerText(),/Unrelated retained record/);
  await page.locator('.patient-retained-sources > summary').click();
  assert.match(await page.locator('.patient-retained-sources').innerText(),/Unrelated retained record: 72 bpm.*Source: other-event/s);
  console.log('PATIENT_MODEL_WORDING_EXACT_CITATIONS_AND_RETAINED_RECORD PASS');
  await page.evaluate(()=>{result.status='BLOCKED';ctx.revision++;dispatchEvent(new Event('aura-record-view'));});await page.waitForTimeout(100);
  assert.equal(await page.locator('.finding-card').count(),0);assert.equal(await page.locator('#assessment-complete').textContent(),'');
  console.log('I9_GUARD_CLEARS_CARDS PASS');
  assert.deepEqual(errors,[]);
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
