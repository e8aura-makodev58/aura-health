/* Once-per-session breathing welcome on the patient home. Synthetic local fixture only. */
'use strict';
const assert=require('node:assert/strict');
const {chromium}=require('playwright');
const base=process.env.AURA_BROWSER_URL;
if(!['127.0.0.1','localhost'].includes(new URL(base).hostname))throw Error('Local synthetic fixture only');
(async()=>{
 const browser=await chromium.launch({headless:true}),context=await browser.newContext({viewport:{width:390,height:844}}),errors=[];
 await context.addInitScript(()=>{window.auraWelcomeInAutomation=true;});
 const page=await context.newPage();page.on('pageerror',e=>errors.push(e.message));
 const loaded=()=>page.waitForFunction(()=>window.auraAgentContext().record&&document.getElementById('notice').hidden);
 try{
  await page.goto(base);await loaded();
  // Clinician view never shows the welcome.
  await page.getByRole('button',{name:'Clinician',exact:true}).click();
  assert.equal(await page.locator('#breath-welcome').isVisible(),false);
  await page.getByRole('button',{name:'Patient',exact:true}).click();
  await page.waitForSelector('#breath-welcome:not([hidden])');
  assert.match(await page.locator('#breath-welcome').innerText(),/Take a breath\.[\s\S]*Continue/);
  assert.equal(await page.locator('#talk').isVisible(),true,'help stays available');
  assert.equal(await page.locator('#month-recap').isVisible(),false,'home content waits behind the welcome');
  await page.locator('#breath-continue').click();
  assert.equal(await page.locator('#breath-welcome').isVisible(),false);
  await page.waitForSelector('#month-recap .patient-recap');
  console.log('WELCOME1_PATIENT_ONLY_HELP_VISIBLE_CONTINUE PASS');
  // Once per session: switching away and back, or reloading, does not repeat it.
  await page.getByRole('button',{name:'Clinician',exact:true}).click();await page.getByRole('button',{name:'Patient',exact:true}).click();
  assert.equal(await page.locator('#breath-welcome').isVisible(),false);
  await page.reload();await loaded();
  assert.equal(await page.locator('#breath-welcome').isVisible(),false);
  console.log('WELCOME2_ONCE_PER_SESSION PASS');
  // Never in front of safety: an active safety panel hides it.
  const fresh=await context.browser().newContext({viewport:{width:390,height:844}});await fresh.addInitScript(()=>{window.auraWelcomeInAutomation=true;});
  const other=await fresh.newPage();other.on('pageerror',e=>errors.push(e.message));
  await other.goto(base);await other.waitForFunction(()=>window.auraAgentContext().record);
  await other.getByRole('button',{name:'Patient',exact:true}).click();await other.waitForSelector('#breath-welcome:not([hidden])');
  await other.evaluate(()=>{document.getElementById('safety-panel').hidden=false;dispatchEvent(new HashChangeEvent('hashchange'));});
  await other.waitForFunction(()=>document.getElementById('breath-welcome').hidden);
  console.log('WELCOME3_SAFETY_FIRST PASS');
  await fresh.close();
  assert.deepEqual(errors,[]);
 }finally{await browser.close();}
})().catch(error=>{console.error(error);process.exit(1);});
