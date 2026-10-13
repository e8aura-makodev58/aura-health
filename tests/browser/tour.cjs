/* Guided story (tour.js): one highlighted thing, one Next button, real results, no repeated actions.
   Synthetic local fixture only. The typed medication question is answered by a stub here because the
   local hosted server accepts only labelled test text; the live site sends it through the safety check. */
'use strict';
const assert=require('node:assert/strict');
const {chromium}=require('playwright');
const base=process.env.AURA_BROWSER_URL;
if(!['127.0.0.1','localhost'].includes(new URL(base).hostname))throw Error('Local synthetic fixture only');
(async()=>{
 const browser=await chromium.launch({headless:true}),errors=[];
 const open=async(width,height)=>{
  const context=await browser.newContext({viewport:{width,height}});
  await context.addInitScript(()=>{window.auraLandingInAutomation=true;window.auraWelcomeInAutomation=true;});
  const page=await context.newPage();page.on('pageerror',e=>errors.push(e.message));
  const doses=[];
  await page.route('**/events',route=>{const body=route.request().postData()||'';if(route.request().method()==='POST'&&/MEDICATION_EVENT/.test(body))doses.push(body);return route.continue();});
  await page.route('**/medication/ask',route=>{const body=JSON.parse(route.request().postData()||'{}');
   if(body.question)return route.fulfill({status:200,contentType:'application/json',body:JSON.stringify({status:'ABSTAINED',topic_id:null,
    answer:"I'm not able to identify that medication, please check with your pharmacist.",source_label:'Approved medication information (development content)',trace:[]})});
   return route.continue();});
  await page.goto(base);await page.waitForFunction(()=>document.getElementById('scenario').options.length>0);
  return {context,page,doses};};
 const ready=page=>page.waitForFunction(()=>{const n=document.querySelector('.tour-next');return n&&!n.disabled;},null,{timeout:180000});
 const step=page=>page.evaluate(()=>window.auraTour.step());
 try{
  let {context,page,doses}=await open(390,844);
  await page.locator('#start-demo').click();await page.waitForSelector('.tour-card');
  assert.match(await page.locator('.tour-title').innerText(),/one person's day/);
  assert.match(await page.locator('.tour-text').innerText(),/fresh demo/);
  assert.equal(await page.locator('.tour-next').innerText(),'Start');
  await page.locator('.tour-next').click();
  // Step 1: the breath; the help button stays above the dimming and clickable.
  await ready(page);assert.equal(await step(page),0);
  assert.match(await page.locator('.tour-chapter').innerText(),/Your day · 1 of 9/);
  const helpOnTop=await page.evaluate(()=>{const t=document.getElementById('talk').getBoundingClientRect();const hit=document.elementFromPoint(t.left+t.width/2,t.top+t.height/2);return Boolean(hit&&hit.closest('#talk'));});
  assert.equal(helpOnTop,true,'help button is not covered');
  await page.locator('.tour-next').click();await ready(page);
  await page.locator('.tour-next').click();await ready(page);
  // Step 3: the tour records the skipped dose itself and shows the saved result.
  assert.equal(await step(page),2);
  assert.match(await page.locator('.tour-status').innerText(),/Saved: skipped, because of side effects/);
  assert.equal(await page.locator('.tour-hole').isVisible(),true,'the dose card is outlined');
  assert.equal(doses.length,1,'one dose event');
  // Back then Next never repeats the action.
  await page.locator('.tour-back').click();await ready(page);await page.locator('.tour-next').click();await ready(page);
  assert.equal(await step(page),2);assert.equal(doses.length,1,'Back/Next did not record another dose');
  console.log('TOUR1_START_HELP_VISIBLE_ONE_DOSE_BACK_SAFE PASS');
  for(let index=3;index<9;index++){
   await page.locator('.tour-next').click();await ready(page);assert.equal(await step(page),index);
   if(index===7){ // no model locally, so the agent falls back: a visible, user-chosen "Ask again" is offered
    assert.match(await page.locator('.tour-status').innerText(),/couldn't complete this answer/);
    await page.locator('.tour-retry').click();await ready(page);
    assert.match(await page.locator('.tour-status').innerText(),/couldn't complete this answer/);
    assert.equal(await step(page),7);
   }
  }
  assert.match(await page.locator('.tour-chapter').innerText(),/When things change · 9 of 9/);
  assert.match(await page.locator('.tour-status').innerText(),/reflects the flu/);
  await page.locator('.tour-next').click();
  await page.waitForFunction(()=>/calm companion/.test(document.querySelector('.tour-title')?.textContent||''));
  for(const label of ['Show the safety example','Explore on my own','Start again'])assert.equal(await page.getByRole('button',{name:label}).isVisible(),true,label);
  console.log('TOUR2_NINE_STEPS_TO_FINISH_PHONE PASS');
  await page.getByRole('button',{name:'Explore on my own'}).click();
  assert.equal(await page.locator('.tour-card').count(),0);assert.equal(await page.locator('.tour-hole').count(),0);
  assert.equal(await page.evaluate(()=>window.auraTour.active()),false);
  console.log('TOUR3_EXIT_REMOVES_EVERYTHING PASS');
  await context.close();
  ({context,page,doses}=await open(1280,900));
  await page.locator('#start-demo').click();await page.waitForSelector('.tour-card');await page.locator('.tour-next').click();await ready(page);
  const box=await page.locator('.tour-card').boundingBox();assert.ok(box.x>640,'card sits at the right on desktop');
  await page.keyboard.press('Escape');assert.equal(await page.locator('.tour-card').count(),0);
  console.log('TOUR4_DESKTOP_AND_ESCAPE PASS');
  await context.close();
  // The safety example explains why the panel stays and offers a reset that clears it.
  ({context,page,doses}=await open(390,844));
  await page.locator('#start-demo').click();await page.waitForSelector('.tour-card');
  await page.evaluate(()=>{window.auraTour.stop();});
  await page.evaluate(()=>window.auraTour.start());await page.locator('.tour-next').click();await ready(page);
  await page.evaluate(()=>window.auraTour.finishForTest());
  await page.getByRole('button',{name:'Show the safety example'}).click();
  await page.waitForFunction(()=>/Safety takes priority/.test(document.querySelector('.tour-title')?.textContent||''),null,{timeout:60000});
  assert.equal(await page.locator('#safety-panel').isVisible(),true);
  assert.match(await page.locator('.tour-text').innerText(),/can't dismiss it/);
  await page.getByRole('button',{name:'Reset the demo'}).click();
  await page.waitForFunction(()=>!document.querySelector('.tour-card'),null,{timeout:60000});
  await page.waitForFunction(()=>document.getElementById('safety-panel').hidden,null,{timeout:30000});
  console.log('TOUR5_SAFETY_EXAMPLE_EXPLAINS_AND_RESETS PASS');
  await context.close();
  assert.deepEqual(errors,[]);
 }finally{await browser.close();}
})().catch(error=>{console.error(error);process.exit(1);});
