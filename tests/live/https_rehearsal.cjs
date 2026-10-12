/* Opt-in synthetic HTTPS UI rehearsal. No runtime changes.
 * NODE_PATH=<existing Playwright modules> AURA_CONFIRM_SYNTHETIC_REHEARSAL=1 node tests/live/https_rehearsal.cjs
 * Optional AURA_BROWSER_URL (HTTPS public host or localhost), AURA_BROWSER_ARTIFACTS (/tmp only).
 * Actual quick/story buttons run unchanged. Only their advance transport receives
 * explicit structured plans, bypassing the LLM director, not the domain engine.
 * Agent headline POSTs are blocked. Ordinary AUTO communication remains on its
 * production path and may call the configured model; it is counted separately.
 */
'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs/promises'),path=require('node:path');
const {chromium}=require('playwright');
const base=new URL(process.env.AURA_BROWSER_URL||'https://aura-health.makodev58.com');
if(process.env.AURA_CONFIRM_SYNTHETIC_REHEARSAL!=='1')throw Error('Explicit synthetic rehearsal confirmation required');
if(base.protocol!=='https:'||!['aura-health.makodev58.com','localhost','127.0.0.1'].includes(base.hostname)||base.username||base.password||base.pathname!=='/'||base.search||base.hash)throw Error('Configured HTTPS synthetic host only');
const out=path.resolve(process.env.AURA_BROWSER_ARTIFACTS||'/tmp/aura-https-rehearsal');
if(!out.startsWith('/tmp/'))throw Error('Artifacts must be in /tmp');
const themes=[['Flu','FLU'],['Travel','TRAVEL'],['Work stress','WORK_STRESS'],['Alcohol','ALCOHOL'],['Missed medication','MISSED_MEDICATION'],['Wearable off','WEARABLE_OFF'],['Exercise','EXERCISE']];
const report={schema:2,origin:base.origin,scope:'Synthetic UI and deterministic domain rehearsal; agent headline POSTs blocked and simulator planner bypassed with explicit plans. Ordinary AUTO communication remains on the production path and may generate through the configured model. No agent headline LIVE AI or generated-swap p95 claim.',method:'Actual UI buttons; advance transport alone injects explicit three-day MODERATE plans, seed42, notesfalse. Chromium HTTP cache disabled, unchanged private workspace, 20 fresh document loads; DOM visibility plus two animation frames measures preview readiness from navigation timeOrigin, not physical screen paint. Communication counters describe browser responses and unique records, not provider call totals; deduplication IDs are kept in memory only.',preflight:{},loads:[],events:[],stories:[],screenshots:[],blocked_agent_posts:0,communication:{responses:0,unique_records:0,generation_attempted:0,generated:0},page_errors:0,failures:[]};
let browser,page,context,phase='preflight',expected=null,lastAdvance=null,patientId;
const assessments={};
const communicationRecords=new Map(),communicationReads=new Set();
const save=()=>fs.writeFile(path.join(out,'metrics.json'),JSON.stringify(report,null,2)+'\n');
const ready=()=>page.waitForFunction(()=>window.auraAgentContext?.().record&&document.getElementById('notice').hidden);
async function preview(role){await page.waitForSelector(role==='clinician'?'#agent-clinician_brief .clinician-finding':'#agent-patient_insight .patient-recap',{state:'visible',timeout:30000});}
async function shots(label){
 for(const role of ['clinician','patient']){
  await page.locator(`#${role}-role`).click();await preview(role);
  for(const width of [390,1280]){
   await page.setViewportSize({width,height:900});assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),'Horizontal overflow');
   const name=`${label}-${role}-${width}.png`;await page.screenshot({path:path.join(out,name),fullPage:true});report.screenshots.push(name);
  }
 }
 // Role switches clear the other assessment DOM. Restore the clinician view so
 // the caller's subsequent snapshot measures its populated finding cards.
 await page.locator('#clinician-role').click();await preview('clinician');
}
async function snapshot(){const data=await page.evaluate(()=>{
 const r=window.auraAgentContext().record;
 return {dates:{start:r.period.start?.slice(0,10),end:r.period.end?.slice(0,10)},channels:r.signals.map(s=>({signal:s.key.signal,sensing:s.current?.sensing_state||null,trust:s.current?.trust_state||null,observations:s.observations.length,findings:s.findings.length,gaps:s.gaps.length,dates:s.observations.map(o=>o.day)})),counts:{checkins:r.checkins.length,medication:r.medication.length,contexts:r.active_context.length,held:r.held.length,questions:r.questions.length,review:r.review_items.length},clinician_cards:document.querySelectorAll('#agent-clinician_brief .clinician-finding').length,patient_visible_measurement_cards:[...document.querySelectorAll('#agent-patient_insight .patient-finding')].filter(n=>n.getClientRects().length).length};
 });return {...data,claimed_counts:structuredClone(assessments)};}
async function seedOptions(){
 await page.locator('#sim-feedback').uncheck();
 const details=page.locator('#life-director [data-technical]');if(!await details.evaluate(n=>n.open))await details.locator(':scope > summary').click();
 await page.locator('#sim-seed').fill('42');
}
async function advance(button,kind){
 expected=kind;lastAdvance=null;
 const responsePromise=page.waitForResponse(r=>new URL(r.url()).pathname.endsWith('/workflows/advance')&&r.request().method()==='POST',{timeout:120000});
 await button.click();const response=await responsePromise;
 assert.equal(response.status(),200,'Advance failed (no retry)');const result=await response.json();
 assert.equal(result.synthetic_only,true);assert.equal(result.status,'EXPLICIT_STRUCTURED_PLAN');assert.equal(result.seed,42);assert.equal(result.plan.days,3);assert.equal(result.notes_enabled,false);
 assert.equal(result.plan.events[0].type,kind);assert.equal(result.plan.events[0].duration_days,3);assert.equal(result.plan.events[0].severity,'MODERATE');
 assert.ok(Array.isArray(result.event_ids));
 await page.waitForFunction(()=>!document.querySelector('[data-workflow]:disabled'),null,{timeout:120000});
 assert.equal(await page.locator('#notice.error').count(),0,'UI workflow error');
 expected=null;return {button:lastAdvance.button,original_options:lastAdvance.original_options,injected_plan:lastAdvance.plan,committed_events:result.event_ids.length,generated_days:result.generated.length,workflow_status:result.status};
}
(async()=>{
 await fs.mkdir(out,{recursive:true});
 try{
  browser=await chromium.launch({headless:true});context=await browser.newContext({viewport:{width:1280,height:900}});page=await context.newPage();
  page.on('pageerror',()=>report.page_errors++);
  page.on('response',async response=>{
   const endpoint=new URL(response.url()).pathname;
   if(/\/events\/[^/]+\/communication$/.test(endpoint)){
    report.communication.responses++;
    const read=(async()=>{
     if(!response.ok())return;
     try{
      const record=await response.json();if(typeof record.communication_id!=='string')return;
      const prior=communicationRecords.get(record.communication_id)||{attempted:false,generated:false};
      if(!communicationRecords.has(record.communication_id))report.communication.unique_records++;
      if(record.generation_attempted===true&&!prior.attempted){prior.attempted=true;report.communication.generation_attempted++;}
      if(record.generation_used===true&&!prior.generated){prior.generated=true;report.communication.generated++;}
      communicationRecords.set(record.communication_id,prior);
     }catch{/* Failed reads do not establish record or generation counts. */}
    })();
    communicationReads.add(read);read.finally(()=>communicationReads.delete(read));
   }
   const match=endpoint.match(/\/assessment\/(clinician_brief|patient_insight)$/);
   if(match&&response.ok())try{const result=await response.json(),draft=result.cached||result.preview;assessments[match[1]]={claims:draft.draft.claims.length,sources:draft.sources.length,headline_fact_count:draft.headline_fact_ids?.length||0,generation_used:Boolean(draft.generation_used)};}catch{/* Loading/closing responses contain no evidence. */}
  });
  for(const [name,endpoint] of [['health','/health'],['status','/system/status'],['catalog','/demo/scenarios']]){
   const response=await context.request.get(new URL(endpoint,base).href);assert.equal(response.status(),200);const data=await response.json();assert.equal(data.synthetic_only,true);report.preflight[name]={http_status:200,synthetic_only:true};
   if(name==='catalog'){assert.ok(data.scenarios.some(r=>r.id==='B'));report.preflight.catalog.cases=data.scenarios.map(r=>r.id);patientId=data.scenarios.find(r=>r.id==='B').patient_id;}
  }
  await page.route('**/patients/*/agent/*',route=>{
   if(route.request().method()!=='POST')return route.continue();report.blocked_agent_posts++;return route.fulfill({status:503,contentType:'application/json',body:'{"error":{"message":"Evaluation uses the committed preview"}}'});
  });
  await page.route('**/patients/*/workflows/advance',route=>{
   const request=route.request();assert.equal(request.method(),'POST');assert.ok(expected,'Unexpected advance; stopped before write');
   const body=request.postDataJSON(),theme=themes.find(([,kind])=>kind===expected);
   assert.equal(body.data.request,theme[0]);assert.equal(body.data.days,3);assert.equal(body.data.notes,false);assert.equal(body.data.seed,42);
   const plan={days:3,events:[{type:expected,start_day:1,duration_days:3,severity:'MODERATE'}],feedback:[]};
   lastAdvance={button:theme[0]==='Flu'?'Simulate: flu 3 days':`Simulate: ${theme[0].toLowerCase()}`,original_options:{days:body.data.days,seed:body.data.seed,notes:body.data.notes},plan};
   return route.continue({postData:JSON.stringify({...body,data:{...body.data,plan}})});
  });
  const cdp=await context.newCDPSession(page);await cdp.send('Network.enable');await cdp.send('Network.setCacheDisabled',{cacheDisabled:true});
  await page.addInitScript(()=>{
   window.__previewDOM=null;
   const observer=new MutationObserver(()=>{
    const node=document.querySelector('#agent-clinician_brief .clinician-finding');
    if(!window.__previewDOM&&node?.getClientRects().length){window.__previewDOM={visible_ms:performance.now()};requestAnimationFrame(()=>requestAnimationFrame(()=>{window.__previewDOM.frames_ms=performance.now();}));}
   });observer.observe(document,{subtree:true,childList:true,attributes:true});
  });
  phase='B screenshots';await page.goto(base.href);await ready();assert.equal(await page.evaluate(()=>window.auraAgentContext().patientId),patientId);await preview('clinician');report.baseline=await snapshot();await shots('B');
  phase='20 cold preview loads';
  for(let i=0;i<20;i++){
   await page.goto(base.href,{waitUntil:'domcontentloaded'});await ready();await preview('clinician');await page.waitForFunction(()=>window.__previewDOM?.frames_ms);
   assert.equal(await page.evaluate(()=>window.auraAgentContext().patientId),patientId,'Private workspace changed');
   report.loads.push({sample:i+1,...await page.evaluate(()=>window.__previewDOM)});await save();
  }
  const values=report.loads.map(r=>r.frames_ms).sort((a,b)=>a-b),p95=values[Math.ceil(.95*values.length)-1];
  report.preview_gate={samples:20,nearest_rank_p95_ms:p95,limit_ms:2000,status:p95<=2000?'PASS':'FAIL',generated_swap_p95:'NOT_MEASURED'};
  for(const [theme,kind] of themes){
   phase=`event ${kind}`;const row={event:kind,status:'STARTED',before:await snapshot()};report.events.push(row);await save();
   await page.locator('#clinician-role').click();await preview('clinician');await page.locator('#demo-toggle').click();await seedOptions();
   Object.assign(row,await advance(page.getByRole('button',{name:theme==='Flu'?'Simulate: flu 3 days':`Simulate: ${theme.toLowerCase()}`,exact:true}),kind));
   await page.locator('#demo-toggle').click();await preview('clinician');assert.equal(await page.evaluate(()=>window.auraAgentContext().patientId),patientId);
   await shots(kind.toLowerCase());row.after=await snapshot();row.status='PASS';await save();
  }
  phase='five story actions';await page.locator('#demo-toggle').click();await seedOptions();
  const story=n=>page.locator('#guided-story button').nth(n-1);
  await story(1).click();await page.waitForFunction(()=>document.getElementById('story-narration').textContent.includes('stable record'));assert.equal(await page.evaluate(()=>document.body.dataset.page),'home');report.stories.push({step:1,status:'PASS'});
  const storyEvent=await advance(story(2),'FLU');await page.waitForFunction(()=>document.getElementById('story-narration').textContent.includes('events are committed'));report.stories.push({step:2,status:'PASS',...storyEvent,button:'2 · A life event'});
  await story(3).click();await page.waitForFunction(()=>document.getElementById('story-narration').textContent.includes('slow-change checkpoint'));assert.equal(await page.evaluate(()=>document.body.dataset.role),'patient');report.stories.push({step:3,status:'PASS'});
  await story(4).click();await page.waitForFunction(()=>document.body.dataset.role==='clinician'&&document.body.dataset.page==='patterns');await preview('clinician');report.stories.push({step:4,status:'PASS'});
  await story(5).click();await page.waitForFunction(()=>document.body.dataset.role==='patient'&&document.body.dataset.page==='review');assert.match(await page.locator('#appointment-preview').innerText(),/Not sent/);report.stories.push({step:5,status:'PASS'});
  await page.locator('#demo-toggle').click();await page.screenshot({path:path.join(out,'story-5-visit.png'),fullPage:true});report.screenshots.push('story-5-visit.png');
  assert.equal(report.page_errors,0,'Page errors');report.status=report.preview_gate.status;
 }catch(error){report.status='FAIL';report.failures.push({phase,kind:error instanceof assert.AssertionError?'ASSERTION':'EXECUTION'});const event=report.events.at(-1);if(event?.status==='STARTED')event.status='FAIL';process.exitCode=1;}
 finally{await Promise.allSettled([...communicationReads]);await save();await browser?.close();console.log(JSON.stringify({status:report.status,phase,events:report.events.length,stories:report.stories.length,artifacts:out,preview_gate:report.preview_gate,communication:report.communication}));if(report.status==='FAIL')process.exitCode=1;}
})();
