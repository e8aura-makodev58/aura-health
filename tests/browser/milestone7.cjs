/* Hosted synthetic workspace gate; use only a local synthetic Docker server. */
"use strict";
const assert = require("node:assert/strict");
const fs = require("node:fs/promises");
const {chromium} = require("playwright");
const base = process.env.AURA_BROWSER_URL || "http://127.0.0.1:8017";
if (!['127.0.0.1','localhost'].includes(new URL(base).hostname)) throw new Error('Local synthetic server required');
async function main() {
  const browser = await chromium.launch({headless:true});
  const context = await browser.newContext({viewport:{width:390,height:844}});
  const other = await browser.newContext();
  const page = await context.newPage(), errors = [], results = [];
  page.on('pageerror', error=>errors.push(error.message));
  page.on('dialog', dialog=>dialog.accept());
  async function check(name, work) { await work(); results.push({name,result:'PASS'}); console.log(`${name} PASS`); }
  try {
    await page.goto(base); await page.waitForSelector('#home-view:not([hidden])');
    const catalog = await (await context.request.get(`${base}/demo/scenarios`)).json();
    const patient = key=>catalog.scenarios.find(item=>item.id===key).patient_id;
    const status = async (client,key)=>(await (await client.get(`${base}/patients/${patient(key)}/status`)).json());
    async function choose(key) {
      if (await page.locator('#demo-panel').isHidden()) await page.locator('#demo-toggle').click();
      await page.locator('#scenario').selectOption(patient(key));
      await page.waitForFunction(()=>!document.getElementById('notice').hidden ? false : !document.getElementById('home-view').hidden);
    }
    await check('HOSTED_NOTICE',async()=>{assert.equal(catalog.hosted,true); await page.locator('#demo-toggle').click(); assert.equal(await page.locator('#hosted-notice').isVisible(),true); assert.equal(await page.locator('#connect').isVisible(),false);});
    await check('CASES_A_F',async()=>{for(const key of 'ABCDEF'){await choose(key); await page.locator('[data-page="patterns"]').click(); assert.equal(await page.locator('.signal-card').count(),4); await page.locator('[data-page="review"]').click(); assert.ok(await page.locator('.review-group').count()>=8); assert.equal((await (await context.request.get(`${base}/patients/${patient(key)}/review-snapshot`)).json()).automatically_sent,false);}});
    await check('SAFETY_PRECEDENCE',async()=>{await choose('F'); assert.equal(await page.locator('#safety-panel').isVisible(),true); assert.equal((await status(context.request,'F')).latest_communication_decision,'SAFETY_REVIEW_REQUIRED');});
    await check('PRIVATE_RESET',async()=>{
      const original=await status(context.request,'stable');
      await other.request.get(`${base}/demo/scenarios`);
      await choose('stable');
      const saved=page.waitForResponse(r=>r.request().method()==='POST'&&new URL(r.url()).pathname.endsWith('/events'));
      await page.locator('[data-checkin="Rough"]').click(); assert.equal((await saved).status(),200);
      await page.waitForFunction(()=>document.getElementById('notice').textContent==='Recorded. Nothing has been sent to a clinician.');
      assert.notDeepEqual(await status(context.request,'stable'),original);
      assert.deepEqual(await status(other.request,'stable'),original);
      if(await page.locator('#demo-panel').isHidden()) await page.locator('#demo-toggle').click();
      const reset=page.waitForResponse(r=>new URL(r.url()).pathname==='/demo/reset');
      await page.locator('#reset-demo').click(); assert.equal((await reset).status(),200);
      await page.waitForFunction(()=>document.getElementById('notice').textContent==='Synthetic session restored. Other visitors were not changed.');
      assert.deepEqual(await status(context.request,'stable'),original);
    });
    await check('NO_REAL_INTAKE',async()=>{
      assert.equal((await context.request.post(`${base}/patients`,{data:{patient_id:'real',display_name:'Synthetic blocked intake',age:35}})).status(),403);
      const before=await (await context.request.get(`${base}/patients/${patient('stable')}/timeline`)).json();
      const id=require('node:crypto').randomUUID();
      assert.equal((await context.request.post(`${base}/patients/${patient('stable')}/events`,{data:{event_id:id,correlation_id:id,idempotency_key:id,event_type:'PATIENT_FREE_TEXT',occurred_at:'2026-01-01T12:00:00+00:00',source:'patient',payload:{text:'unapproved arbitrary input'}}})).status(),403);
      assert.deepEqual(await (await context.request.get(`${base}/patients/${patient('stable')}/timeline`)).json(),before);
    });
    await check('SURFACE_RESTRICTION',async()=>{for(const route of ['/docs','/redoc','/openapi.json','/assets/README.md']) assert.equal((await context.request.get(base+route)).status(),404);});
    assert.deepEqual(errors,[]);
    await fs.mkdir('/tmp/aura-m7-browser-artifacts',{recursive:true});
    await page.screenshot({path:'/tmp/aura-m7-browser-artifacts/hosted-mobile.png',fullPage:true});
    await fs.writeFile('/tmp/aura-m7-browser-artifacts/results.json',JSON.stringify({results,errors},null,2));
  } finally {await context.close();await other.close();await browser.close();}
}
main().catch(error=>{console.error(error);process.exitCode=1;});
