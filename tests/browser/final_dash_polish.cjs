'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs/promises');
const {chromium}=require('playwright');
const base=process.env.AURA_BROWSER_URL,out=process.env.AURA_BROWSER_ARTIFACTS;
if(!['127.0.0.1','localhost'].includes(new URL(base).hostname))throw Error('Local synthetic fixture only');
(async()=>{
 await fs.mkdir(out,{recursive:true});const browser=await chromium.launch({headless:true}),context=await browser.newContext({viewport:{width:1280,height:900}}),page=await context.newPage(),errors=[];
 page.on('pageerror',e=>errors.push(e.message));
 const loaded=()=>page.waitForFunction(()=>window.auraAgentContext().record&&document.getElementById('notice').hidden);
 const story=number=>page.locator('#guided-story button').nth(number-1);
 try{
  await page.goto(base);await loaded();await page.waitForSelector('#agent-clinician_brief .clinician-finding');
  assert.deepEqual(await page.locator('#evidence-charts > .chart-card').evaluateAll(nodes=>nodes.map(n=>n.dataset.signal)),['SLEEP_MIDPOINT','SLEEP_DURATION','ACTIVITY','RESTING_HEART_RATE']);
  if(await page.locator('#other-measurements').count()){
   assert.equal(await page.locator('#other-measurements').evaluate(n=>n.open),false);
   assert.match(await page.locator('#other-measurements > summary').innerText(),/Other measurements \(\d+\)/);
  }
  for(const id of ['workspace-evidence','workspace-context','workspace-details'])assert.match(await page.locator(`#${id}>summary .disclosure-count`).innerText(),/^\d+$/);
  // A chart with fewer than three actual readings moves into the optional group.
  await page.evaluate(()=>{const record=structuredClone(window.auraAgentContext().record);record.signals.find(s=>s.key.signal==='SLEEP_DURATION').observations=record.signals.find(s=>s.key.signal==='SLEEP_DURATION').observations.slice(-2);window.renderAuraEvidence(record);});
  assert.equal(await page.locator('#other-measurements .chart-card[data-signal="SLEEP_DURATION"]').count(),1);
  assert.match(await page.locator('#other-measurements > summary').innerText(),/Other measurements \(\d+\)/);
  assert.equal(await page.locator('#other-measurements .chart-card[data-signal="SLEEP_DURATION"]').isVisible(),false);
  await page.evaluate(()=>window.renderAuraEvidence(window.auraAgentContext().record));
  console.log('FD_POLISH1_CHART_GROUPS_SPARSE_COLLAPSE_COUNTS PASS');
  await page.locator('#patient-role').click();await page.waitForSelector('#agent-patient_insight .patient-recap');
  for(const width of [1280,390]){
   await page.setViewportSize({width,height:900});
   assert.equal(await page.locator('#home-heading').innerText(),'Your day, with AURA');
   assert.ok(await page.locator('#month-recap').isVisible());
   assert.doesNotMatch(await page.locator('#home-view').innerText(),/\d{4}-\d{2}-\d{2}|steady · reports|RMSSD|HRV|Recent change|AI-written|What AURA has noticed/);
   assert.equal(await page.locator('#agent-patient_insight .patient-finding:visible').count(),0);
   assert.equal(await page.locator('#agent-patient_insight .patient-summary-details').evaluate(n=>n.open),false);
   assert.match(await page.locator('#appointment-ready').innerText(),/\d+ items? ready · Not sent/);
   assert.ok(await page.locator('#patient-help').isVisible());
   assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
   await page.screenshot({path:`${out}/polish-patient-${width}.png`,fullPage:true});
  }
  await page.locator('#appointment-card').click();await page.waitForSelector('#review-view:not([hidden])');assert.match(await page.locator('#appointment-preview').innerText(),/Not sent/);
  await page.locator('#patient-role').click();await page.locator('#demo-toggle').click();
  assert.equal(await page.locator('#demo-panel').evaluate(n=>getComputedStyle(n).position),'fixed');
  assert.ok(await page.locator('#demo-panel').evaluate(n=>n.getBoundingClientRect().height<=innerHeight*.43));
  console.log('FD_POLISH2_PATIENT_PHONE_DESKTOP_APPOINTMENT_HELP PASS');
  await story(1).click();await page.waitForFunction(()=>document.getElementById('story-narration').textContent.includes('starts with a breath'));assert.equal(await page.evaluate(()=>document.body.dataset.page),'home');assert.equal(await page.evaluate(()=>document.body.dataset.role),'patient');
  await story(2).click();await page.waitForFunction(()=>document.getElementById('story-narration').textContent.includes('Skipped'));assert.equal(await page.evaluate(()=>document.body.dataset.role),'patient');
  await page.locator('#sim-feedback').uncheck();const previous=await page.evaluate(()=>window.auraAgentContext().revision);
  await story(3).click();await page.waitForFunction(()=>document.getElementById('story-narration').textContent.includes('changed record'),null,{timeout:90000});assert.notEqual(await page.evaluate(()=>window.auraAgentContext().revision),previous);
  await story(4).click();await page.waitForFunction(()=>document.body.dataset.role==='patient'&&document.body.dataset.page==='review');assert.match(await page.locator('#appointment-preview').innerText(),/Not sent/);
  await story(5).click();await page.waitForFunction(()=>document.body.dataset.role==='clinician'&&document.body.dataset.page==='patterns');await page.waitForSelector('#agent-clinician_brief .clinician-finding');
  assert.equal(await page.locator('#agent-question-text').inputValue(),'When did sleep timing change, and was anything reported around then?');
  await story(6).click();await page.waitForFunction(()=>document.getElementById('input-dialog').open);assert.equal(await page.evaluate(()=>document.body.dataset.role),'patient');
  await page.keyboard.press('Escape');
  await page.locator('#demo-toggle').click();
  console.log('FD_POLISH3_SIX_ACTUAL_STORY_ACTIONS PASS');
  assert.deepEqual(errors,[]);
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
