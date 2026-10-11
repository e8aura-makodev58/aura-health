/* Opt-in HTTPS synthetic demo check. Assistant POSTs are blocked: preview only. */
'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs/promises');
const {chromium}=require('playwright');
if(!process.argv.includes('--confirm-live-synthetic-checks'))throw Error('Explicit synthetic live confirmation required');
const base='https://aura-health.makodev58.com',out='/tmp/aura-final-dash-https';
(async()=>{
 await fs.mkdir(out,{recursive:true});const browser=await chromium.launch({headless:true}),context=await browser.newContext({viewport:{width:1280,height:900}}),page=await context.newPage(),errors=[];
 page.on('pageerror',e=>errors.push(e.message));
 try{
  const health=await(await context.request.get(base+'/health')).json();assert.equal(health.synthetic_only,true);
  await page.route('**/patients/*/agent/*',route=>route.fulfill({status:503,contentType:'application/json',body:'{"error":{"message":"Live browser uses committed preview; model measured separately"}}'}));
  await page.goto(base);await page.waitForSelector('.clinician-finding');
  await page.locator('#demo-toggle').click();await page.locator('#sim-feedback').uncheck();
  await page.getByRole('button',{name:'Simulate: flu 3 days',exact:true}).click();
  await page.waitForFunction(()=>document.getElementById('notice').textContent.includes('Flu:'),null,{timeout:120000});
  await page.locator('#demo-toggle').click();
  for(const signal of ['RESTING_HEART_RATE','HRV','RESPIRATORY_RATE','SKIN_TEMPERATURE_DEVIATION'])await page.locator(`.clinician-finding[data-signal="${signal}"]`).waitFor({state:'visible'});
  for(const role of ['clinician','patient']){
   await page.locator(`#${role}-role`).click();await page.waitForSelector(`#agent-${role==='clinician'?'clinician_brief':'patient_insight'} .finding-card`);
   for(const width of [1280,390]){await page.setViewportSize({width,height:900});assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));await page.screenshot({path:`${out}/flu-${role}-${width}.png`,fullPage:true});}
  }
  assert.deepEqual(errors,[]);console.log('HTTPS_FLU_PREVIEW_BOTH_ROLES_PHONE_LAPTOP PASS; no assistant model calls; one synthetic director call');
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
