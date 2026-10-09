'use strict';
const assert=require('node:assert/strict');
const {chromium}=require('playwright');
const fs=require('node:fs/promises');
const base=process.env.AURA_BROWSER_URL,out=process.env.AURA_BROWSER_ARTIFACTS;
if(!['localhost','127.0.0.1'].includes(new URL(base).hostname))throw Error('Synthetic local test only');
(async()=>{
 await fs.mkdir(out,{recursive:true});const browser=await chromium.launch({headless:true});
 const context=await browser.newContext({viewport:{width:390,height:844}}),page=await context.newPage(),errors=[];
 page.on('pageerror',e=>errors.push(e.message));
 try{
  await page.goto(base);await page.waitForSelector('#patterns-view:not([hidden])');
  await page.locator('#system-settings').click();await page.waitForFunction(()=>!document.getElementById('settings-current-model').textContent.includes('Loading'));
  assert.match(await page.locator('#settings-current-model').innerText(),/Offline fallback/);await page.locator('#close-settings').click();console.log('AW_UI1_PROVIDER_BEFORE_UNLOCK PASS');
  await page.locator('.info-link').click();await page.waitForSelector('#about-view:not([hidden])');assert.match(await page.locator('#about-view').innerText(),/Technical demonstration|Technical/);await page.evaluate(()=>location.hash='patterns');
  await page.locator('#manual-intake>summary').click();await page.locator('#manual-form [data-signal="BODY_TEMPERATURE"]').fill('38.2');await page.locator('#manual-form button').click();
  await page.waitForFunction(()=>document.getElementById('notice').textContent.includes('Measurements recorded'));
  assert.equal(await page.locator('#evidence-charts [data-signal="BODY_TEMPERATURE"] .chart-observed').count(),1);console.log('AW_UI2_MANUAL_AND_CHART PASS');
  await page.locator('#manual-intake details>summary').click();await page.locator('#manual-intake textarea').first().fill('date,RESTING_HEART_RATE\n2026-03-11,67');
  await page.getByRole('button',{name:'Propose column mapping',exact:true}).click();await page.waitForSelector('#import-mapping:not([hidden])');
  assert.match(await page.locator('#import-mapping').inputValue(),/RESTING_HEART_RATE/);await page.getByRole('button',{name:'Confirm mapping and import',exact:true}).click();
  await page.waitForFunction(()=>document.getElementById('notice').textContent.includes('Import committed'));console.log('AW_UI3_CONFIRMED_IMPORT PASS');
  await page.locator('#demo-toggle').click();await page.locator('#auto-assessment').uncheck();await page.locator('#sim-feedback').uncheck();
  await page.getByRole('button',{name:'Flu',exact:true}).click();await page.getByRole('button',{name:'Advance 3 days',exact:true}).click();
  await page.waitForFunction(()=>document.getElementById('notice').textContent.includes('Advanced 3 days'),null,{timeout:90000});
  assert.ok(await page.locator('#evidence-charts .chart-card').count()>=11);assert.equal(await page.locator('#evidence-charts [data-signal="HRV"]').count(),1);await page.getByRole('button',{name:'Verify deterministic replay',exact:true}).click();
  await page.waitForFunction(()=>document.getElementById('notice').textContent.includes('Replay matched'));console.log('AW_UI4_OFFLINE_LIFE_DIRECTOR_REPLAY PASS');
  for(const width of [320,390,1280]){await page.setViewportSize({width,height:900});assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+2));}
  await page.locator('#demo-toggle').click();await page.locator('#patient-role').click();assert.equal(await page.locator('#life-director').isVisible(),false);
  await page.getByRole('link',{name:'Prepare for my appointment'}).click();await page.waitForSelector('#review-view:not([hidden])');assert.equal(await page.locator('#print-visit-pack').isVisible(),true);
  await page.screenshot({path:`${out}/approved-workflows.png`,fullPage:true});assert.deepEqual(errors,[]);console.log('AW_UI5_MOBILE_LAPTOP_PRINT_AND_GUIDE_ISOLATION PASS');
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
