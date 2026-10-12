'use strict';
const assert=require('node:assert/strict');
const fs=require('node:fs/promises');
const {chromium}=require('playwright');
const base=process.env.AURA_BROWSER_URL;
const out=process.env.AURA_BROWSER_ARTIFACTS||'/tmp/aura-plain-language';
if(!['localhost','127.0.0.1'].includes(new URL(base).hostname))throw Error('Local synthetic fixtures only');
(async()=>{
 await fs.mkdir(out,{recursive:true});
 const browser=await chromium.launch({headless:true}),page=await browser.newPage(),errors=[];
 page.on('pageerror',e=>errors.push(e.message));
 try{
  await page.goto(base);await page.waitForFunction(()=>window.auraAgentContext().record&&document.getElementById('notice').hidden);
  const terms=await (await page.request.get(base+'/assets/plain_terms.json')).json();
  const catalog=await page.evaluate(()=>catalog);
  async function lint(role,label){
   const failures=await page.evaluate(({terms,role})=>{
    const bad=[],walker=document.createTreeWalker(document.body,NodeFilter.SHOW_TEXT);
    let text;
    while((text=walker.nextNode())){const parent=text.parentElement;if(!parent||parent.closest('[data-technical],#safety-panel,#settings-dialog,#about-view')||!parent.checkVisibility({checkVisibilityCSS:true})||!text.textContent.trim())continue;
     // Closed details descendants do not count as visible evidence.
     if(parent.closest('details:not([open])')&&!parent.closest('summary'))continue;
     const value=text.textContent,patterns=(terms[role]||[]).map(({term})=>[term,new RegExp('\\b'+term.replace(/[.*+?^${}()|[\]\\]/g,'\\$&')+'\\b','i')]);
     patterns.push(['internal code',/\b[A-Z][A-Z0-9]+_[A-Z0-9_]+\b/],['fact ID',/\bf\d+\b/],['event ID',/\bdemo-[A-F]-\d+-\S+/]);
     if(role==='patient')patterns.push(['ISO date',/\b\d{4}-\d{2}-\d{2}\b/],['exclamation',/!/]);
     for(const [term,pattern] of patterns)if(pattern.test(value))bad.push(`${term}: ${parent.tagName.toLowerCase()}#${parent.id}.${parent.className}: ${value}`);
    }return bad;
   },{terms,role});assert.deepEqual(failures,[],label);
   if(role==='patient')for(const recap of await page.locator('.patient-recap:visible').allTextContents()){const sentences=recap.split(/[.!?]+/).filter(s=>s.trim());assert.ok(sentences.reduce((sum,s)=>sum+s.trim().split(/\s+/).length,0)/Math.max(1,sentences.length)<=16,`${label}: sentence length ${recap}`);}
  }
  async function inspect(label){
   for(const width of [1280,390]){
    await page.setViewportSize({width,height:900});
    await page.locator('#clinician-role').click();await page.waitForFunction(()=>document.getElementById('agent-clinician_brief').textContent.trim());await page.waitForLoadState('networkidle');
    await lint('clinician',label+' clinician '+width);
    const facts=await page.evaluate(()=>window.auraAgentContext().record.signals.filter(s=>s.current));
    for(const signal of facts){const chart=page.locator(`.chart-card[data-signal="${signal.key.signal}"]`).first();if(await chart.isVisible())assert.match(await chart.innerText(),new RegExp(`${signal.current.rolling.sample_count} readings`));}
    const exact=page.locator('#agent-clinician_brief .finding-exact');if(await exact.count())assert.match(await exact.first().innerText(),/Difference: -?\d.*(?:minutes|hours|steps|bpm|beats|°C|ms|breaths)/);
    if(label==='Case B')await page.screenshot({path:`${out}/plain-clinician-exact-${width}.png`,fullPage:true});
    await page.locator('#patient-role').click();await page.waitForFunction(()=>document.getElementById('agent-patient_insight').textContent.trim());await page.waitForLoadState('networkidle');await lint('patient',label+' patient '+width);
    if(label==='Case B')await page.screenshot({path:`${out}/plain-patient-home-${width}.png`,fullPage:true});
    for(const selector of ['.patient-summary-details > summary','.patient-summary-sources > summary','.patient-retained-sources > summary']){const fold=page.locator('#agent-patient_insight '+selector);if(await fold.count()&&await fold.isVisible()){if(!await fold.evaluate(n=>n.parentElement.open))await fold.click();assert.equal(await fold.evaluate(n=>n.parentElement.open),true,label+' source disclosure stays open');if(label==='Case B'&&selector==='.patient-summary-sources > summary')await page.screenshot({path:`${out}/plain-patient-why-${width}.png`,fullPage:true});}}
    await lint('patient',label+' patient sources '+width);
    await page.getByRole('link',{name:/See my full data/}).click();await lint('patient',label+' patient full data '+width);
    assert.equal(await page.locator('#agent-workspace').isVisible(),false);
    await page.evaluate(()=>{location.hash='review';});await page.waitForSelector('#review-view:not([hidden])');await lint('patient',label+' patient appointment '+width);
    assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
   }
  }
  for(const scenario of catalog.filter(row=>['A','B','C','D','E','F'].includes(row.id))){await page.evaluate(async id=>loadPatient(id),scenario.patient_id);await inspect('Case '+scenario.id);}
  console.log('PLAIN1_CASES_A_F_PHONE_LAPTOP_FACTS_SOURCES PASS');
  await page.evaluate(async id=>loadPatient(id),catalog.find(row=>row.id==='B').patient_id);
  for(const event of ['Flu','Travel','Work stress','Alcohol','Missed medication','Wearable off','Exercise']){
   await page.evaluate(async request=>{const ctx=window.auraAgentContext();const response=await fetch(`/patients/${encodeURIComponent(ctx.patientId)}/workflows/advance`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({run_id:window.auraUniqueId(),data:{days:3,seed:7,request,notes:false}})});if(!response.ok)throw Error('Fixture advance failed');await refresh();},event);
   await inspect(event);
  }
  console.log('PLAIN2_SEVEN_LIFE_EVENTS_PHONE_LAPTOP PASS');assert.deepEqual(errors,[]);
 }finally{await browser.close();}
})().catch(error=>{console.error(error);process.exitCode=1;});
