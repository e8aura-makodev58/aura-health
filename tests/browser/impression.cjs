'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs/promises');
const {chromium}=require('playwright');
const base=process.env.AURA_BROWSER_URL,out=process.env.AURA_BROWSER_ARTIFACTS;
if(!['localhost','127.0.0.1'].includes(new URL(base).hostname))throw Error('Local synthetic test only');
(async()=>{
 await fs.mkdir(out,{recursive:true});const browser=await chromium.launch({headless:true});
 const context=await browser.newContext({viewport:{width:390,height:844},reducedMotion:'reduce'}),page=await context.newPage(),errors=[],posts=[];
 page.on('pageerror',e=>errors.push(e.message));page.on('request',r=>{if(r.method()==='POST'&&r.url().includes('/agent/'))posts.push(r.postDataJSON());});
 try{
  await page.goto(base);await page.waitForSelector('#agent-clinician_brief .agent-claim');
  assert.ok(await page.locator('#agent-clinician_brief h3').isVisible());assert.ok(await page.locator('#agent-clinician_brief .agent-claim').count()>=2);
  assert.ok(await page.locator('#agent-clinician_brief .agent-claim').count()<=3);
  assert.equal(await page.locator('#agent-clinician_brief .finding-card').count(),await page.locator('#agent-clinician_brief .agent-claim').count());
  assert.doesNotMatch(await page.locator('#agent-clinician_brief').innerText(),/\d+\.\d{3}\b/);
  assert.equal(await page.locator('#agent-query').isVisible(),false);
  await page.waitForTimeout(800);assert.equal(posts.filter(p=>p.run_id.startsWith('arrival-')).length,1);console.log('I1_ARRIVAL_IMMEDIATE_CACHED_ASSESSMENT PASS');
  assert.equal(await page.locator('#agent-question-text').isVisible(),true);assert.equal(await page.locator('.suggested-questions button').count(),3);
  assert.equal(await page.locator('#patterns-view > details.workspace-disclosure').count(),3);
  await page.locator('.suggested-questions button').first().click();await page.waitForSelector('#agent-record_qa .agent-disclosure');console.log('I4_VISIBLE_SOURCED_QUESTIONS_I5_THREE_GROUPS PASS');
  await page.locator('#patient-role').click();await page.waitForSelector('#month-recap:not([hidden]) .patient-recap');
  assert.equal(await page.locator('#home-view svg').count(),0);assert.doesNotMatch(await page.locator('#agent-patient_insight').innerText(),/\b(?:baseline|drift|anchor)\b/i);
  const recapHeading=await page.locator('.patient-recap').boundingBox();assert.ok(recapHeading.y>=0&&recapHeading.y+recapHeading.height<844);
  assert.ok(await page.locator('#agent-patient_insight .agent-claim').count()<=3);assert.doesNotMatch(await page.locator('#agent-patient_insight').innerText(),/\d{4}-\d{2}-\d{2}|Recorded changes/);await page.screenshot({path:`${out}/impression-patient-390.png`,fullPage:true});
  await page.locator('#clinician-role').click();await page.waitForSelector('#agent-clinician_brief .agent-claim');await page.waitForTimeout(300);
  assert.equal(posts.filter(p=>p.run_id.startsWith('arrival-')&&p.window_days===56).length,1);console.log('I6_DEFAULT_TEXT_RECAP_NO_HOME_CHARTS PASS');
  for(const width of [320,390,1280]){await page.setViewportSize({width,height:900});assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));await page.screenshot({path:`${out}/impression-clinician-${width}.png`,fullPage:true});}
  await context.setOffline(true);await page.waitForSelector('#safety-panel:not([hidden])');assert.equal(await page.locator('#assessment-complete').textContent(),'');assert.equal(await page.locator('#agent-visit_prep').textContent(),'');assert.equal(await page.locator('.story-finding-band').count(),0);console.log('I1_OFFLINE_CLEARS_PERMITTED_CONTENT PASS');
  await context.setOffline(false);await page.waitForFunction(()=>document.getElementById('safety-panel').hidden);
  await page.locator('#demo-toggle').click();assert.equal(await page.locator('#guided-story button').count(),6);
  await page.getByRole('button',{name:'4 · Ready for the appointment',exact:true}).click();await page.waitForSelector('#review-view:not([hidden])');assert.match(await page.locator('.sharing-note').innerText(),/Not sent/);console.log('I7_GUIDED_VISIT_NOT_SENT PASS');
  assert.deepEqual(errors,[]);
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
