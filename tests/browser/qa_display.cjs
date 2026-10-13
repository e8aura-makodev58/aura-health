/* Record Q&A display: exact clinician facts, visible fallback reason. Mocked responses, no provider calls. */
'use strict';
const assert=require('node:assert/strict'),path=require('node:path');
const {chromium}=require('playwright');
(async()=>{
 const browser=await chromium.launch({headless:true}),page=await browser.newPage({viewport:{width:1280,height:900}}),errors=[];
 page.on('pageerror',e=>errors.push(e.message));
 try{
  await page.setContent('<input id="agent-question-text" value="What was recorded?"><select id="agent-query"><option value="sleep_change">x</option></select><button data-agent-role="record_qa">Ask</button><div id="agent-record_qa"></div><section id="appointment-preview"></section>');
  await page.evaluate(()=>{
   window.auraPlain=text=>String(text??'').replace(/\b(\d{4})-(\d{2})-(\d{2})\b/g,(_,y,m,d)=>`${Number(d)} ${['Jan','Feb','Mar'][Number(m)-1]} ${y}`);
   window.auraTechnical=(...children)=>{const fold=document.createElement('details');fold.dataset.technical='';fold.append(...children);return fold;};
   window.ctx={patientId:'synthetic',revision:1,role:'clinician',offline:false,record:{signals:[],checkins:[]}};
   window.auraAgentContext=()=>window.ctx;window.auraUniqueId=()=>'00000000-0000-4000-8000-000000000000';
   window.result={status:'COMPLETE',state_fingerprint:'fp',generation_used:false,reason:'INVALID_OR_UNAVAILABLE_MODEL',
    disclosure:"The demo's shared AI limit for this minute was reached, so these are related facts from the record. Try again shortly.",
    draft:{headline:'Related facts from the record',claims:[{text:'Heart rate variability recorded 2026-03-01: 48.234 ms.',fact_ids:['f1'],findings:[],section:'changes'}],question_ids:[]},
    sources:[{fact_id:'f1',source_ref:'hrv-event',text:'Heart rate variability recorded 2026-03-01: 48.234 ms.'}],question_options:{},trace:[],investigation:['Read the readings and changes for Activity','Compared Activity: 2026-02-26 to 2026-03-11 with 2026-02-12 to 2026-02-25']};
   window.fetch=async url=>({ok:true,json:async()=>String(url).includes('/assessment/')?{generation_allowed:true,state_fingerprint:'fp'}:window.result});
  });
  await page.addScriptTag({path:path.resolve('aura_ui/agent.js')});
  await page.locator('[data-agent-role="record_qa"]').click();
  await page.waitForSelector('#agent-record_qa .agent-claim');
  const text=await page.locator('#agent-record_qa').innerText();
  assert.match(text,/48\.234 ms/);assert.match(text,/1 Mar 2026/);assert.doesNotMatch(text,/early March|48\.2 ms/);
  assert.match(await page.locator('#agent-record_qa .agent-disclosure-text').innerText(),/shared AI limit for this minute/);
  assert.match(await page.locator('#agent-record_qa .investigation-trail').innerText(),/How AURA looked: Read the readings and changes for Activity → Compared Activity: 26 Feb 2026 to 11 Mar 2026 with 12 Feb 2026 to 25 Feb 2026/);
  console.log('QA1_EXACT_CLINICIAN_FACTS_AND_VISIBLE_REASON PASS');
  // Loading presentation: patient preview shows at once, a small note while wording is pending, nothing afterwards.
  const patientPage='<section id="home-view"><div id="recap-placeholder" hidden>breathing</div><section id="month-recap" hidden><div id="agent-patient_insight"></div></section></section><section id="appointment-preview"></section>';
  for(const mode of ['generated','blocked','error']){
   await page.setContent(patientPage);
   await page.evaluate(mode=>{
    window.auraPlain=text=>String(text??'');window.auraTechnical=(...c)=>{const f=document.createElement('details');f.append(...c);return f;};
    window.ctx={patientId:'synthetic',revision:1,role:'patient',offline:false,record:{period:{start:'2026-01-01',end:'2026-03-11'},signals:[],checkins:[]}};
    window.auraAgentContext=()=>window.ctx;window.auraUniqueId=()=>'u';window.linkAuraStoryFindings=()=>{};window.clearAuraStory=()=>{};
    const finding={signal:'SLEEP_MIDPOINT',direction:'LATER',since:'2026-02-23'};
    const preview={status:mode==='blocked'?'BLOCKED':'COMPLETE',state_fingerprint:'fp',generation_used:false,headline_fact_ids:[],
     draft:{headline:mode==='blocked'?'':'Your sleep time was later than your usual.',claims:mode==='blocked'?[]:[{text:'Your sleep time was later than your usual.',fact_ids:['f1'],findings:[{fact_id:'f1',...finding}]}],question_ids:[]},
     sources:[{fact_id:'f1',source_ref:'e',text:'x',patient:{text:'Your sleep time was later than your usual.',recap_text:'Your sleep time was later than your usual.',source_label:'Your measurements',date_label:'23 Feb – 11 Mar'},finding,at:'2026-03-11'}],question_options:{},trace:[]};
    window.release=null;
    window.fetch=async(url,options)=>{
     if(mode==='error')return {ok:false,json:async()=>({error:{message:'unavailable'}})};
     if(options?.method==='POST'){await new Promise(r=>window.release=r);return {ok:true,json:async()=>({...preview,generation_used:true,draft:{...preview.draft,headline:'Your sleep time has been later recently.'},headline_fact_ids:['f1']})};}
     return {ok:true,json:async()=>({preview,run_id:'arrival-x',window_days:56,generation_allowed:mode==='generated'})};};
   },mode);
   await page.addScriptTag({path:path.resolve('aura_ui/agent.js')});
   await page.evaluate(()=>{window.refreshAuraAssessment();});
   if(mode==='generated'){
    await page.waitForSelector('.recap-pending');assert.equal(await page.locator('#recap-placeholder').isHidden(),true);
    await page.evaluate(()=>window.release());await page.waitForFunction(()=>!document.querySelector('.recap-pending'));
   }else await page.waitForTimeout(300);
   assert.equal(await page.locator('#recap-placeholder').isHidden(),true,mode);
   assert.equal(await page.locator('.recap-pending').count(),0,mode);
  }
  console.log('QA2_LOADING_NEVER_OUTLIVES_REQUEST PASS');
  assert.deepEqual(errors,[]);
 }finally{await browser.close();}
})().catch(error=>{console.error(error);process.exit(1);});
