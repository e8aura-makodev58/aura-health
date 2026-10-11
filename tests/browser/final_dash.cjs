'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs/promises');
const {chromium}=require('playwright');
const base=process.env.AURA_BROWSER_URL,out=process.env.AURA_BROWSER_ARTIFACTS;
if(!['127.0.0.1','localhost'].includes(new URL(base).hostname))throw Error('Local synthetic fixture only');
(async()=>{
 await fs.mkdir(out,{recursive:true});const browser=await chromium.launch({headless:true}),context=await browser.newContext({viewport:{width:1280,height:900}}),page=await context.newPage(),errors=[];
 page.on('pageerror',e=>errors.push(e.message));
 const unique=async()=>{
  const channels=await page.locator('#agent-clinician_brief .clinician-finding').evaluateAll(nodes=>nodes.map(n=>n.dataset.channel));
  assert.equal(new Set(channels).size,channels.length);
 };
 try{
  await page.goto(base);await page.waitForSelector('#agent-clinician_brief .clinician-finding');
  const synthesis=await page.locator('#agent-clinician_brief .assessment-synthesis').innerText();
  assert.match(synthesis,/Sleep timing/);assert.match(synthesis,/Activity/);assert.match(synthesis,/Check-ins/);
  assert.doesNotMatch(synthesis,/\bbecause\b|\bdue to\b|\bled to\b/i);
  assert.match(await page.locator('.clinician-checkins').innerText(),/patient-reported/i);
  await unique();assert.match(await page.locator('.agent-disclosure').first().innerText(),/Summary from the record/);
  const catalog=await(await context.request.get(base+'/demo/scenarios')).json();
  await page.locator('#demo-toggle').click();
  for(const key of ['A','B','C','D','E','F']){
   const row=catalog.scenarios.find(r=>r.id===key);
   await page.locator('#scenario').selectOption(row.patient_id);
   await page.waitForFunction(id=>window.auraAgentContext().patientId===id&&document.getElementById('notice').hidden,row.patient_id);
   await page.waitForTimeout(250);await unique();
  }
  console.log('FD_BROWSER1_EXACT_CHANNEL_UNIQUENESS_A_F PASS');
  await page.locator('#scenario').selectOption(catalog.scenarios.find(r=>r.id==='B').patient_id);
  await page.waitForFunction(()=>document.getElementById('notice').hidden);await page.waitForTimeout(300);
  await page.locator('#sim-feedback').uncheck();
  await page.getByRole('button',{name:'Simulate: flu 3 days',exact:true}).click();
  await page.waitForFunction(()=>document.getElementById('notice').textContent.includes('Flu:'),null,{timeout:90000});
  for(const signal of ['RESTING_HEART_RATE','HRV','RESPIRATORY_RATE','SKIN_TEMPERATURE_DEVIATION','SLEEP_MIDPOINT','ACTIVITY']){
   const card=page.locator(`#agent-clinician_brief .finding-card[data-signal="${signal}"]`);
   await card.waitFor({state:'visible'});assert.equal(await card.count(),1);
   if(['RESTING_HEART_RATE','HRV','RESPIRATORY_RATE','SKIN_TEMPERATURE_DEVIATION'].includes(signal))assert.match(await card.innerText(),/Recent change/);
  }
  await unique();assert.match(await page.locator('.reading-item[data-signal="BODY_TEMPERATURE"]').innerText(),/Thermometer temperature.*3 readings/);
  assert.match(await page.locator('#agent-clinician_brief .assessment-synthesis').innerText(),/HRV/);
  await page.locator('#demo-toggle').click();
  for(const width of [1280,390]){await page.setViewportSize({width,height:900});assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));await page.screenshot({path:`${out}/final-dash-flu-clinician-${width}.png`,fullPage:true});}
  console.log('FD_BROWSER2_FLU_SIX_CHANNELS_AND_SPARSE_READINGS PASS');
  await page.locator('#patient-role').click();
  await page.waitForSelector('#agent-patient_insight .more-changes');
  assert.equal(await page.locator('#agent-patient_insight>.finding-grid .patient-finding:not(.steady-report)').count(),2);
  assert.ok(await page.locator('#agent-patient_insight .patient-recap').isVisible());
  assert.match(await page.locator('#agent-patient_insight>.finding-grid .patient-finding').first().innerText(),/recent change/i);
  assert.equal(await page.locator('#agent-patient_insight .assessment-synthesis').count(),0);
  assert.equal(await page.locator('#agent-patient_insight .question-copy').count(),0);
  await page.locator('#agent-patient_insight .more-changes summary').click();
  assert.ok(await page.locator('#agent-patient_insight .more-changes .patient-finding:visible').count()>=4);
  assert.doesNotMatch(await page.locator('#agent-patient_insight').innerText(),/\d{4}-\d{2}-\d{2}/);
  await page.screenshot({path:`${out}/final-dash-flu-patient-390.png`,fullPage:true});
  console.log('FD_BROWSER3_PATIENT_TWO_DEFAULT_AND_ONE_TAP_ALL PASS');
  assert.deepEqual(errors,[]);
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
