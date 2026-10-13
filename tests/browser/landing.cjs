/* Landing stays until the visitor chooses a view. Synthetic local fixture only. */
'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs/promises');
const {chromium}=require('playwright');
const base=process.env.AURA_BROWSER_URL,out=process.env.AURA_BROWSER_ARTIFACTS;
if(!['127.0.0.1','localhost'].includes(new URL(base).hostname))throw Error('Local synthetic fixture only');
(async()=>{
 await fs.mkdir(out,{recursive:true});
 const browser=await chromium.launch({headless:true}),errors=[];
 const open=async(width,height)=>{const context=await browser.newContext({viewport:{width,height}});
  await context.addInitScript(()=>{window.auraLandingInAutomation=true;window.auraWelcomeInAutomation=true;});
  const page=await context.newPage();page.on('pageerror',e=>errors.push(e.message));
  await page.goto(base);await page.waitForFunction(()=>document.getElementById('scenario').options.length>0);return {context,page};};
 try{
  for(const [w,h] of [[390,844],[1280,900]]){
   const {context,page}=await open(w,h);await page.waitForTimeout(1200);
   assert.equal(await page.locator('#empty-state').isVisible(),true,'landing stays');
   assert.equal(await page.evaluate(()=>document.body.classList.contains('on-landing')),true);
   assert.equal(await page.evaluate(()=>window.auraAgentContext().record),undefined,'no record opened yet');
   assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
   await page.screenshot({path:`${out}/landing-${w}.png`});await context.close();
  }
  console.log('LANDING1_STAYS_UNTIL_CHOICE PASS');
  let {context,page}=await open(390,844);
  await page.locator('#start-patient').click();await page.waitForSelector('#home-view:not([hidden])');
  assert.equal(await page.evaluate(()=>document.body.dataset.role),'patient');
  assert.equal(await page.locator('#breath-welcome').isVisible(),true,'patient choice leads to the breathing welcome');
  assert.equal(await page.evaluate(()=>document.body.classList.contains('on-landing')),false);
  await context.close();
  ({context,page}=await open(1280,900));
  await page.locator('#start-clinician').click();await page.waitForSelector('#patterns-view:not([hidden])');
  assert.equal(await page.evaluate(()=>document.body.dataset.role),'clinician');await context.close();
  ({context,page}=await open(1280,900));
  await page.locator('#start-demo').click();await page.waitForSelector('#home-view:not([hidden])');assert.equal(await page.evaluate(()=>document.body.dataset.role),'patient');
  assert.equal(await page.locator('#demo-panel').isVisible(),true,'story guide opens');await context.close();
  ({context,page}=await open(1280,900));
  await page.getByRole('button',{name:'Patient',exact:true}).click();await page.waitForSelector('#home-view:not([hidden])');await context.close();
  console.log('LANDING2_TILES_AND_ROLE_BUTTONS_OPEN_DEMO PASS');
  assert.deepEqual(errors,[]);
 }finally{await browser.close();}
})().catch(error=>{console.error(error);process.exit(1);});
